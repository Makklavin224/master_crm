"""Receipt service: Robokassa ReceiptAttach for cash/card payments.

Issues fiscal receipts via Robokassa RoboFiscal API for payments made
outside Robokassa (cash, card-to-card). Includes retry logic and
notification helpers.
"""

import logging
import uuid

import httpx
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.booking import Booking
from app.models.client import Client, ClientPlatform
from app.models.master import Master
from app.models.payment import Payment
from app.services.encryption_service import decrypt_value
from app.services.robokassa_service import RobokassaCredentials, RobokassaService

logger = logging.getLogger(__name__)

RECEIPT_ATTACH_URL = "https://ws.roboxchange.com/RoboFiscal/Receipt/Attach"


class ReceiptService:
    """Stateless service for issuing fiscal receipts via Robokassa ReceiptAttach."""

    @staticmethod
    async def send_receipt_attach(
        db: AsyncSession,
        payment_id: uuid.UUID,
    ) -> bool:
        """Send a ReceiptAttach request to Robokassa for a given payment.

        Loads payment with booking->service, booking->client relations.
        Validates master has Robokassa connected with INN/FNS.
        Makes HTTP POST to RoboFiscal ReceiptAttach endpoint.

        On success: sets receipt_status='issued', saves fns_receipt_url.
        On failure: increments fns_receipt_attempts; if >= 3, sets 'failed'.

        Returns:
            True if receipt was successfully issued, False otherwise.
        """
        # Load payment with relations
        result = await db.execute(
            select(Payment)
            .where(Payment.id == payment_id)
            .options(
                selectinload(Payment.booking).selectinload(Booking.service),
                selectinload(Payment.booking).selectinload(Booking.client),
            )
        )
        payment = result.scalar_one_or_none()
        if not payment:
            logger.error("ReceiptAttach: payment %s not found", payment_id)
            return False

        # Load master
        master_result = await db.execute(
            select(Master).where(Master.id == payment.master_id)
        )
        master = master_result.scalar_one_or_none()
        if not master:
            logger.error("ReceiptAttach: master not found for payment %s", payment_id)
            return False

        # Validate: Robokassa connected + INN + FNS
        if not master.robokassa_merchant_login:
            logger.warning("ReceiptAttach: Robokassa not connected for master %s", master.id)
            return False
        if not master.inn or not master.fns_connected:
            logger.warning("ReceiptAttach: INN/FNS not configured for master %s", master.id)
            return False

        # Decrypt credentials
        password1 = decrypt_value(master.robokassa_password1_encrypted or "")
        password2 = decrypt_value(master.robokassa_password2_encrypted or "")
        if not password1 or not password2:
            logger.error("ReceiptAttach: failed to decrypt credentials for master %s", master.id)
            return False

        creds = RobokassaCredentials(
            merchant_login=master.robokassa_merchant_login,
            password1=password1,
            password2=password2,
            is_test=master.robokassa_is_test,
            hash_algorithm=master.robokassa_hash_algorithm,
        )

        # Build payload
        service_name = "Service"
        if payment.booking and payment.booking.service:
            service_name = payment.booking.service.name

        client_phone = None
        if payment.booking and payment.booking.client:
            client_phone = payment.booking.client.phone

        amount_rub = f"{payment.amount / 100:.2f}"

        payload = RobokassaService.build_receipt_attach_payload(
            creds=creds,
            service_name=service_name,
            amount_rub=amount_rub,
            sno=master.receipt_sno,
            client_phone=client_phone,
        )

        # Make HTTP POST
        try:
            async with httpx.AsyncClient(timeout=30.0) as client_http:
                response = await client_http.post(
                    RECEIPT_ATTACH_URL,
                    json=payload,
                )

            if response.status_code == 200:
                resp_data = response.json()
                result_code = resp_data.get("ResultCode", -1)

                if result_code == 0:
                    # Success
                    payment.receipt_status = "issued"
                    receipt_url = resp_data.get("OpKey") or resp_data.get("ReceiptUrl")
                    if receipt_url:
                        payment.fns_receipt_url = str(receipt_url)
                    await db.flush()
                    logger.info(
                        "ReceiptAttach success for payment %s", payment_id
                    )
                    return True
                else:
                    logger.warning(
                        "ReceiptAttach failed for payment %s: ResultCode=%s, %s",
                        payment_id,
                        result_code,
                        resp_data.get("ResultDescription", ""),
                    )
            else:
                logger.warning(
                    "ReceiptAttach HTTP %d for payment %s",
                    response.status_code,
                    payment_id,
                )

        except Exception:
            logger.exception("ReceiptAttach HTTP error for payment %s", payment_id)

        # Failure path: increment attempts
        payment.fns_receipt_attempts += 1
        if payment.fns_receipt_attempts >= 3:
            payment.receipt_status = "failed"
        await db.flush()
        return False

    @staticmethod
    async def get_client_platform_for_notification(
        db: AsyncSession,
        payment: Payment,
    ) -> tuple[str, str] | None:
        """Find the client's messenger platform for notification delivery.

        Priority: uses booking's source_platform, falls back to telegram > max > vk.

        Returns:
            Tuple of (platform, platform_user_id) or None if not found.
        """
        # Load booking to get client_id and source_platform
        booking_result = await db.execute(
            select(Booking)
            .where(Booking.id == payment.booking_id)
            .options(selectinload(Booking.client))
        )
        booking = booking_result.scalar_one_or_none()
        if not booking or not booking.client:
            return None

        client_id = booking.client.id
        source_platform = booking.source_platform or "telegram"

        # Try source platform first
        cp_result = await db.execute(
            select(ClientPlatform).where(
                and_(
                    ClientPlatform.client_id == client_id,
                    ClientPlatform.platform == source_platform,
                )
            )
        )
        cp = cp_result.scalar_one_or_none()
        if cp:
            return (cp.platform, cp.platform_user_id)

        # Fallback: try telegram > max > vk
        for fallback_platform in ("telegram", "max", "vk"):
            if fallback_platform == source_platform:
                continue
            fb_result = await db.execute(
                select(ClientPlatform).where(
                    and_(
                        ClientPlatform.client_id == client_id,
                        ClientPlatform.platform == fallback_platform,
                    )
                )
            )
            fb = fb_result.scalar_one_or_none()
            if fb:
                return (fb.platform, fb.platform_user_id)

        return None


async def process_pending_receipts() -> None:
    """Poll for pending receipts and retry ReceiptAttach.

    Runs as APScheduler job every 5 minutes.
    For each pending receipt with < 3 attempts:
    - Retries ReceiptAttach
    - On success: sends receipt link to client
    - On final failure (3 attempts): notifies master
    """
    from app.bots.common.notification import notification_service
    from app.core.database import async_session_factory

    try:
        async with async_session_factory() as session:
            # Query pending receipts with auto fiscalization and < 3 attempts
            result = await session.execute(
                select(Payment)
                .where(
                    and_(
                        Payment.receipt_status == "pending",
                        Payment.fns_receipt_attempts < 3,
                        Payment.fiscalization_level == "auto",
                    )
                )
                .options(
                    selectinload(Payment.booking).selectinload(Booking.service),
                    selectinload(Payment.booking).selectinload(Booking.client),
                )
            )
            payments = result.scalars().all()

            for payment in payments:
                try:
                    success = await ReceiptService.send_receipt_attach(
                        session, payment.id
                    )

                    if success and payment.fns_receipt_url:
                        # Send receipt link to client
                        platform_info = await ReceiptService.get_client_platform_for_notification(
                            session, payment
                        )
                        if platform_info:
                            platform, platform_user_id = platform_info
                            service_name = "Service"
                            if payment.booking and payment.booking.service:
                                service_name = payment.booking.service.name
                            await notification_service.send_receipt_link(
                                platform=platform,
                                platform_user_id=platform_user_id,
                                receipt_url=payment.fns_receipt_url,
                                service_name=service_name,
                            )

                    elif payment.fns_receipt_attempts >= 3:
                        # All retries exhausted -- notify master
                        service_name = "Service"
                        client_name = "Client"
                        if payment.booking:
                            if payment.booking.service:
                                service_name = payment.booking.service.name
                            if payment.booking.client:
                                client_name = payment.booking.client.name

                        # Load master for notification
                        master_result = await session.execute(
                            select(Master).where(Master.id == payment.master_id)
                        )
                        master = master_result.scalar_one_or_none()
                        if master and master.tg_user_id:
                            error_text = (
                                f"Не удалось выдать чек для {service_name} "
                                f"({client_name}). Оформите чек вручную "
                                f"в 'Мой Налог'."
                            )
                            await notification_service.send_message(
                                platform="telegram",
                                platform_user_id=master.tg_user_id,
                                text=error_text,
                            )

                except Exception:
                    logger.exception(
                        "Error processing receipt for payment %s",
                        payment.id,
                    )

            await session.commit()

    except Exception:
        logger.exception("Error in process_pending_receipts")
