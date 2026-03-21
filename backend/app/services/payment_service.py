"""Payment service: orchestrates manual, Robokassa, and requisites payment flows.

Handles payment creation, status transitions, Robokassa callback processing,
and fiscalization data preparation.
"""

import json
import logging
import uuid
from datetime import date, datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import and_, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.booking import Booking
from app.models.master import Master
from app.models.payment import Payment
from app.services.encryption_service import decrypt_value
from app.services.qr_service import generate_payment_qr
from app.services.robokassa_service import RobokassaCredentials, RobokassaService

logger = logging.getLogger(__name__)


class PaymentService:
    """Orchestrates all three payment flows with proper status management."""

    @staticmethod
    async def _load_payment_with_rels(
        db: AsyncSession, payment_id: uuid.UUID
    ) -> Payment:
        """Reload a payment with booking->service and booking->client eagerly loaded."""
        result = await db.execute(
            select(Payment)
            .where(Payment.id == payment_id)
            .options(
                selectinload(Payment.booking).selectinload(Booking.service),
                selectinload(Payment.booking).selectinload(Booking.client),
            )
        )
        return result.scalar_one()

    @staticmethod
    async def _load_booking(
        db: AsyncSession,
        master_id: uuid.UUID,
        booking_id: uuid.UUID,
    ) -> Booking:
        """Load and validate a booking for payment.

        Checks: booking exists, belongs to master, status is 'confirmed'.
        """
        result = await db.execute(
            select(Booking)
            .where(
                and_(
                    Booking.id == booking_id,
                    Booking.master_id == master_id,
                )
            )
            .options(
                selectinload(Booking.service),
                selectinload(Booking.client),
            )
        )
        booking = result.scalar_one_or_none()

        if booking is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Booking not found",
            )

        if booking.status != "confirmed":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Booking status is '{booking.status}', expected 'confirmed'",
            )

        return booking

    @staticmethod
    def _get_effective_fiscalization(
        master: Master,
        override: str | None,
    ) -> str:
        """Determine the effective fiscalization level.

        Per-payment override takes priority over master's default.
        """
        if override is not None:
            return override
        return master.fiscalization_level

    @staticmethod
    def format_receipt_data(
        amount_kopecks: int,
        service_name: str,
        client_name: str,
    ) -> dict:
        """Format payment data for manual receipt entry in 'Moy Nalog'.

        Returns a dict with formatted display values.
        """
        amount_rub = amount_kopecks / 100
        return {
            "amount_display": f"{amount_rub:,.2f} rub".replace(",", " "),
            "service_name": service_name,
            "client_name": client_name,
            "date": datetime.now(timezone.utc).strftime("%d.%m.%Y"),
        }

    @staticmethod
    async def create_manual_payment(
        db: AsyncSession,
        master: Master,
        booking_id: uuid.UUID,
        payment_method: str,
        fiscalization_override: str | None = None,
        amount_override: int | None = None,
    ) -> Payment:
        """Create a manual payment: master records payment received.

        Flow: validate booking -> create Payment(status=paid) -> mark booking completed.
        If fiscalization is 'manual', populates receipt_data JSON.
        If amount_override is set, uses it instead of the service price.
        """
        booking = await PaymentService._load_booking(db, master.id, booking_id)

        effective_fisc = PaymentService._get_effective_fiscalization(
            master, fiscalization_override
        )
        now = datetime.now(timezone.utc)

        # Determine final amount
        final_amount = amount_override if amount_override is not None else booking.service.price

        # Build receipt data for manual fiscalization
        receipt_data_json = None
        receipt_status = "not_applicable"
        if effective_fisc == "manual":
            receipt_data_json = json.dumps(
                PaymentService.format_receipt_data(
                    amount_kopecks=final_amount,
                    service_name=booking.service.name,
                    client_name=booking.client.name if booking.client else "Client",
                ),
                ensure_ascii=False,
            )
            receipt_status = "pending"  # awaiting manual entry in "Moy Nalog"

        payment = Payment(
            master_id=master.id,
            booking_id=booking.id,
            amount=final_amount,
            status="paid",
            payment_method=payment_method,
            receipt_status=receipt_status,
            fiscalization_level=effective_fisc,
            receipt_data=receipt_data_json,
            paid_at=now,
        )
        db.add(payment)

        # Mark booking as completed
        booking.status = "completed"

        await db.flush()

        return await PaymentService._load_payment_with_rels(db, payment.id)

    @staticmethod
    async def create_robokassa_payment(
        db: AsyncSession,
        master: Master,
        booking_id: uuid.UUID,
        fiscalization_override: str | None = None,
        amount_override: int | None = None,
    ) -> Payment:
        """Create a Robokassa payment: generate signed payment URL.

        Flow: validate booking -> decrypt credentials -> get InvId from sequence ->
        build receipt JSON if auto -> generate URL -> create Payment(status=pending).
        If amount_override is set, uses it instead of the service price.
        """
        booking = await PaymentService._load_booking(db, master.id, booking_id)

        # Validate Robokassa is connected
        if not master.robokassa_merchant_login:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Robokassa is not connected. Configure it in Settings.",
            )

        # Decrypt credentials
        password1 = decrypt_value(master.robokassa_password1_encrypted or "")
        password2 = decrypt_value(master.robokassa_password2_encrypted or "")
        if not password1 or not password2:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to decrypt Robokassa credentials. Please reconfigure in Settings.",
            )

        creds = RobokassaCredentials(
            merchant_login=master.robokassa_merchant_login,
            password1=password1,
            password2=password2,
            is_test=master.robokassa_is_test,
            hash_algorithm=master.robokassa_hash_algorithm,
        )

        effective_fisc = PaymentService._get_effective_fiscalization(
            master, fiscalization_override
        )

        # Determine final amount
        final_amount = amount_override if amount_override is not None else booking.service.price

        # Get next InvId from sequence
        result = await db.execute(text("SELECT nextval('robokassa_inv_id_seq')"))
        inv_id = result.scalar_one()

        # Amount in rubles (from kopecks)
        amount_rub = f"{final_amount / 100:.2f}"

        # Build receipt JSON if auto fiscalization
        receipt_json = None
        receipt_status = "not_applicable"
        if effective_fisc == "auto":
            receipt_json = RobokassaService.build_receipt_json(
                service_name=booking.service.name,
                amount_rub=amount_rub,
                sno=master.receipt_sno,
            )
            receipt_status = "pending"

        # Custom params for callback routing
        shp_params = {
            "Shp_booking_id": str(booking.id),
            "Shp_master_id": str(master.id),
        }

        # Generate signed payment URL
        description = f"Оплата: {booking.service.name}"
        payment_url = RobokassaService.generate_payment_url(
            creds=creds,
            inv_id=inv_id,
            out_sum=amount_rub,
            description=description,
            receipt_json=receipt_json,
            shp_params=shp_params,
        )

        payment = Payment(
            master_id=master.id,
            booking_id=booking.id,
            amount=final_amount,
            status="pending",
            payment_method="sbp_robokassa",
            receipt_status=receipt_status,
            fiscalization_level=effective_fisc,
            robokassa_inv_id=inv_id,
            payment_url=payment_url,
        )
        db.add(payment)

        await db.flush()

        return await PaymentService._load_payment_with_rels(db, payment.id)

    @staticmethod
    async def create_requisites_payment(
        db: AsyncSession,
        master: Master,
        booking_id: uuid.UUID,
        fiscalization_override: str | None = None,
    ) -> tuple[Payment, dict]:
        """Create a requisites payment: show QR code with master's payment info.

        Flow: validate booking -> generate QR from sbp_phone or card_number ->
        create Payment(status=pending) -> return payment + requisites data.

        Returns:
            Tuple of (Payment, requisites_dict) where requisites_dict contains
            card_number, sbp_phone, bank_name, qr_code_base64.
        """
        booking = await PaymentService._load_booking(db, master.id, booking_id)

        # Validate master has payment requisites
        if not master.sbp_phone and not master.card_number:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No payment requisites configured. Add card number or SBP phone in Settings.",
            )

        # Generate QR code (prefer SBP phone)
        qr_data = master.sbp_phone or master.card_number or ""
        qr_base64 = generate_payment_qr(qr_data)

        effective_fisc = PaymentService._get_effective_fiscalization(
            master, fiscalization_override
        )

        payment = Payment(
            master_id=master.id,
            booking_id=booking.id,
            amount=booking.service.price,
            status="pending",
            payment_method=None,  # set on confirmation
            receipt_status="not_applicable",
            fiscalization_level=effective_fisc,
        )
        db.add(payment)

        await db.flush()

        loaded_payment = await PaymentService._load_payment_with_rels(db, payment.id)

        requisites = {
            "card_number": master.card_number,
            "sbp_phone": master.sbp_phone,
            "bank_name": master.bank_name,
            "qr_code_base64": qr_base64,
        }

        return loaded_payment, requisites

    @staticmethod
    async def confirm_requisites_payment(
        db: AsyncSession,
        master: Master,
        payment_id: uuid.UUID,
        payment_method: str = "sbp",
    ) -> Payment:
        """Confirm a pending requisites payment: master marks as paid.

        Flow: validate payment is pending -> set paid -> mark booking completed ->
        handle fiscalization.
        """
        result = await db.execute(
            select(Payment)
            .where(
                and_(
                    Payment.id == payment_id,
                    Payment.master_id == master.id,
                )
            )
            .with_for_update()
        )
        payment = result.scalar_one_or_none()

        if payment is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payment not found",
            )

        if payment.status != "pending":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Payment status is '{payment.status}', expected 'pending'",
            )

        now = datetime.now(timezone.utc)
        payment.status = "paid"
        payment.paid_at = now
        payment.payment_method = payment_method

        # Handle fiscalization
        effective_fisc = payment.fiscalization_level or master.fiscalization_level
        if effective_fisc == "manual":
            # Load booking with service and client for receipt data
            booking_result = await db.execute(
                select(Booking)
                .where(Booking.id == payment.booking_id)
                .options(
                    selectinload(Booking.service),
                    selectinload(Booking.client),
                )
            )
            booking = booking_result.scalar_one_or_none()
            if booking:
                payment.receipt_data = json.dumps(
                    PaymentService.format_receipt_data(
                        amount_kopecks=payment.amount,
                        service_name=booking.service.name if booking.service else "Service",
                        client_name=booking.client.name if booking.client else "Client",
                    ),
                    ensure_ascii=False,
                )
                payment.receipt_status = "pending"
                booking.status = "completed"
        else:
            # Mark booking completed
            booking_result = await db.execute(
                select(Booking).where(Booking.id == payment.booking_id)
            )
            booking = booking_result.scalar_one_or_none()
            if booking:
                booking.status = "completed"

        await db.flush()

        return await PaymentService._load_payment_with_rels(db, payment.id)

    @staticmethod
    async def handle_robokassa_callback(
        db: AsyncSession,
        master_id: str,
        inv_id: int,
        out_sum: str,
        signature: str,
        shp_params: dict[str, str] | None = None,
    ) -> bool:
        """Handle Robokassa ResultURL callback with idempotency.

        Flow: look up payment by inv_id -> idempotency check -> decrypt credentials ->
        verify signature -> update payment + booking status.

        Returns:
            True if payment was processed (or already processed), False if
            signature verification failed.
        """
        # Look up payment by robokassa_inv_id
        result = await db.execute(
            select(Payment)
            .where(Payment.robokassa_inv_id == inv_id)
            .with_for_update()
        )
        payment = result.scalar_one_or_none()

        if payment is None:
            logger.warning(
                "Robokassa callback for unknown InvId=%d", inv_id
            )
            return False

        # Idempotency: already paid, return success without re-processing
        if payment.status == "paid":
            logger.info(
                "Robokassa callback for already-paid payment InvId=%d", inv_id
            )
            return True

        # Load master to get credentials
        master_result = await db.execute(
            select(Master).where(Master.id == payment.master_id)
        )
        master = master_result.scalar_one_or_none()
        if master is None:
            logger.error(
                "Master not found for payment InvId=%d, master_id=%s",
                inv_id,
                master_id,
            )
            return False

        # Decrypt credentials
        password1 = decrypt_value(master.robokassa_password1_encrypted or "")
        password2 = decrypt_value(master.robokassa_password2_encrypted or "")
        if not password1 or not password2:
            logger.error(
                "Failed to decrypt Robokassa credentials for master %s",
                master_id,
            )
            return False

        creds = RobokassaCredentials(
            merchant_login=master.robokassa_merchant_login or "",
            password1=password1,
            password2=password2,
            is_test=master.robokassa_is_test,
            hash_algorithm=master.robokassa_hash_algorithm,
        )

        # Verify signature
        if not RobokassaService.verify_result_signature(
            creds=creds,
            out_sum=out_sum,
            inv_id=str(inv_id),
            received_signature=signature,
            shp_params=shp_params,
        ):
            logger.warning(
                "Invalid signature for Robokassa callback InvId=%d", inv_id
            )
            return False

        # Update payment status
        now = datetime.now(timezone.utc)
        payment.status = "paid"
        payment.paid_at = now

        # If auto fiscalization, receipt was sent with the payment URL
        # Robochecks handles receipt generation automatically
        effective_fisc = payment.fiscalization_level or master.fiscalization_level
        if effective_fisc == "auto":
            payment.receipt_status = "issued"

        # Mark booking as completed
        booking_result = await db.execute(
            select(Booking).where(Booking.id == payment.booking_id)
        )
        booking = booking_result.scalar_one_or_none()
        if booking:
            booking.status = "completed"

        await db.flush()

        logger.info(
            "Robokassa payment confirmed: InvId=%d, amount=%s",
            inv_id,
            out_sum,
        )

        return True

    @staticmethod
    async def get_payment_history(
        db: AsyncSession,
        master_id: uuid.UUID,
        status_filter: str | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
        payment_method: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[dict], int, int]:
        """Query payment history with filters and pagination.

        Joins with booking -> service, booking -> client for display names.

        Returns:
            Tuple of (payment_dicts, total_count, total_revenue).
            total_revenue is the sum of amounts for paid payments matching the filters.
        """
        from app.models.client import Client
        from app.models.service import Service

        # Base conditions (shared between main query and revenue query)
        conditions = [Payment.master_id == master_id]
        if status_filter:
            conditions.append(Payment.status == status_filter)
        if date_from:
            conditions.append(func.date(Payment.created_at) >= date_from)
        if date_to:
            conditions.append(func.date(Payment.created_at) <= date_to)
        if payment_method:
            conditions.append(Payment.payment_method == payment_method)

        # Base query with joins
        base_query = (
            select(Payment)
            .where(and_(*conditions))
            .options(
                selectinload(Payment.booking).selectinload(Booking.service),
                selectinload(Payment.booking).selectinload(Booking.client),
            )
        )

        # Count total
        count_query = select(func.count()).select_from(
            base_query.subquery()
        )
        total_result = await db.execute(count_query)
        total = total_result.scalar_one()

        # Total revenue: sum of paid payment amounts matching the same filters
        revenue_conditions = [
            Payment.master_id == master_id,
            Payment.status == "paid",
        ]
        if date_from:
            revenue_conditions.append(func.date(Payment.created_at) >= date_from)
        if date_to:
            revenue_conditions.append(func.date(Payment.created_at) <= date_to)
        if payment_method:
            revenue_conditions.append(Payment.payment_method == payment_method)
        revenue_query = select(
            func.coalesce(func.sum(Payment.amount), 0)
        ).where(and_(*revenue_conditions))
        revenue_result = await db.execute(revenue_query)
        total_revenue = revenue_result.scalar_one()

        # Fetch paginated results
        data_query = (
            base_query
            .order_by(Payment.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await db.execute(data_query)
        payments = list(result.scalars().all())

        # Build response dicts with display names
        items = []
        for payment in payments:
            item = {
                "id": payment.id,
                "booking_id": payment.booking_id,
                "amount": payment.amount,
                "status": payment.status,
                "payment_method": payment.payment_method,
                "receipt_status": payment.receipt_status,
                "fiscalization_level": payment.fiscalization_level,
                "paid_at": payment.paid_at,
                "created_at": payment.created_at,
                "payment_url": payment.payment_url,
                "service_name": None,
                "client_name": None,
            }
            if payment.booking:
                if payment.booking.service:
                    item["service_name"] = payment.booking.service.name
                if payment.booking.client:
                    item["client_name"] = payment.booking.client.name
            items.append(item)

        return items, total, total_revenue

    @staticmethod
    async def cancel_payment(
        db: AsyncSession,
        master: Master,
        payment_id: uuid.UUID,
    ) -> Payment:
        """Cancel a payment. Updates receipt status if applicable.

        For Robokassa payments with issued receipts, sets receipt_status
        to 'cancelled' (actual receipt annulment is reminder-only in v1).
        """
        result = await db.execute(
            select(Payment)
            .where(
                and_(
                    Payment.id == payment_id,
                    Payment.master_id == master.id,
                )
            )
            .with_for_update()
        )
        payment = result.scalar_one_or_none()

        if payment is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payment not found",
            )

        if payment.status == "cancelled":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Payment is already cancelled",
            )

        payment.status = "cancelled"

        # Handle receipt cancellation
        if payment.receipt_status == "issued":
            payment.receipt_status = "cancelled"
            # v1: receipt cancellation is reminder-only, no API call
            # For Robokassa: master will be reminded to cancel in dashboard
            # For manual: master will be reminded to cancel in "Moy Nalog"

        await db.flush()

        return await PaymentService._load_payment_with_rels(db, payment.id)
