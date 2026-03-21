"""Payment API endpoints: manual, Robokassa, requisites flows + history."""

import csv
import io
import json
import uuid
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_master, get_db_with_rls
from app.models.master import Master
from app.schemas.payment import (
    ManualReceiptData,
    PaymentConfirm,
    PaymentCreate,
    PaymentListResponse,
    PaymentRead,
    PaymentRequisites,
    RequisitesPaymentCreate,
    RobokassaPaymentCreate,
)
from app.services.payment_service import PaymentService

router = APIRouter()


def _payment_to_read(payment, **extra) -> PaymentRead:
    """Convert Payment model to PaymentRead schema."""
    data = {
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
        "fns_receipt_url": payment.fns_receipt_url,
    }
    # Add display fields from booking relationships if loaded
    if hasattr(payment, "booking") and payment.booking:
        if payment.booking.service:
            data["service_name"] = payment.booking.service.name
        if payment.booking.client:
            data["client_name"] = payment.booking.client.name
    data.update(extra)
    return PaymentRead(**data)


@router.post("/manual", response_model=PaymentRead)
async def create_manual_payment(
    data: PaymentCreate,
    master: Annotated[Master, Depends(get_current_master)],
    db: Annotated[AsyncSession, Depends(get_db_with_rls)],
):
    """Create a manual payment: master records payment received."""
    payment = await PaymentService.create_manual_payment(
        db=db,
        master=master,
        booking_id=data.booking_id,
        payment_method=data.payment_method,
        fiscalization_override=data.fiscalization_level,
        amount_override=data.amount_override,
    )

    # Fire-and-forget: ReceiptAttach for auto fiscalization
    if payment.receipt_status == "pending" and payment.fiscalization_level == "auto":
        try:
            from app.bots.common.notification import notification_service
            from app.services.receipt_service import ReceiptService

            success = await ReceiptService.send_receipt_attach(db, payment.id)
            if success and payment.fns_receipt_url:
                # Reload payment to get updated fns_receipt_url
                await db.refresh(payment)
                # Send receipt link to client
                platform_info = await ReceiptService.get_client_platform_for_notification(
                    db, payment
                )
                if platform_info:
                    platform, platform_user_id = platform_info
                    service_name = "Service"
                    if hasattr(payment, "booking") and payment.booking:
                        if payment.booking.service:
                            service_name = payment.booking.service.name
                    await notification_service.send_message(
                        platform=platform,
                        platform_user_id=platform_user_id,
                        text=f'Чек по услуге "{service_name}":\n{payment.fns_receipt_url}',
                    )
        except Exception:
            import logging

            logging.getLogger(__name__).exception(
                "Failed to send ReceiptAttach for manual payment"
            )

    return _payment_to_read(payment)


@router.post("/robokassa", response_model=PaymentRead)
async def create_robokassa_payment(
    data: RobokassaPaymentCreate,
    master: Annotated[Master, Depends(get_current_master)],
    db: Annotated[AsyncSession, Depends(get_db_with_rls)],
):
    """Create a Robokassa payment: generate signed payment URL and send link to client."""
    payment = await PaymentService.create_robokassa_payment(
        db=db,
        master=master,
        booking_id=data.booking_id,
        fiscalization_override=data.fiscalization_level,
        amount_override=data.amount_override,
    )

    # Fire-and-forget: send payment link to client via notification
    try:
        from sqlalchemy import and_, select
        from sqlalchemy.orm import selectinload

        from app.bots.common.notification import notification_service
        from app.models.booking import Booking
        from app.models.client import ClientPlatform

        result = await db.execute(
            select(Booking)
            .where(Booking.id == data.booking_id)
            .options(
                selectinload(Booking.client),
                selectinload(Booking.service),
            )
        )
        booking = result.scalar_one_or_none()
        if booking and booking.client:
            # Look up telegram platform user ID from client_platforms
            cp_result = await db.execute(
                select(ClientPlatform).where(
                    and_(
                        ClientPlatform.client_id == booking.client.id,
                        ClientPlatform.platform == "telegram",
                    )
                )
            )
            tg_platform = cp_result.scalar_one_or_none()
            if tg_platform:
                amount_rub = payment.amount / 100
                amount_display = f"{amount_rub:,.2f} \u20bd".replace(",", " ")
                service_name = booking.service.name if booking.service else "Service"
                await notification_service.send_payment_link(
                    platform="telegram",
                    platform_user_id=tg_platform.platform_user_id,
                    payment_url=payment.payment_url or "",
                    service_name=service_name,
                    amount_display=amount_display,
                )
    except Exception:
        import logging

        logging.getLogger(__name__).exception(
            "Failed to send payment link notification"
        )

    return _payment_to_read(payment)


@router.post("/requisites", response_model=PaymentRead)
async def create_requisites_payment(
    data: RequisitesPaymentCreate,
    master: Annotated[Master, Depends(get_current_master)],
    db: Annotated[AsyncSession, Depends(get_db_with_rls)],
):
    """Create a requisites payment: show QR code with master's payment info."""
    payment, requisites = await PaymentService.create_requisites_payment(
        db=db,
        master=master,
        booking_id=data.booking_id,
        fiscalization_override=data.fiscalization_level,
    )
    read = _payment_to_read(payment)
    # Attach requisites data to response
    read_dict = read.model_dump()
    read_dict["requisites"] = PaymentRequisites(**requisites).model_dump()
    return read_dict


@router.get("/export-csv")
async def export_payments_csv(
    master: Annotated[Master, Depends(get_current_master)],
    db: Annotated[AsyncSession, Depends(get_db_with_rls)],
    status_filter: str | None = Query(default=None, alias="status"),
    payment_method: str | None = Query(default=None),
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
):
    """Export filtered payments as a CSV file."""
    items, total, _ = await PaymentService.get_payment_history(
        db=db,
        master_id=master.id,
        status_filter=status_filter,
        date_from=date_from,
        date_to=date_to,
        payment_method=payment_method,
        limit=10000,
        offset=0,
    )

    method_labels = {
        "cash": "Наличные",
        "card_to_card": "Перевод на карту",
        "sbp": "СБП",
        "sbp_robokassa": "СБП (Robokassa)",
    }
    status_labels = {
        "pending": "Ожидание",
        "paid": "Оплачен",
        "cancelled": "Отменён",
        "refunded": "Возврат",
    }
    receipt_labels = {
        "not_applicable": "Не требуется",
        "pending": "Ожидание",
        "issued": "Выдан",
        "failed": "Ошибка",
    }

    output = io.StringIO()
    output.write("\ufeff")  # BOM for Excel UTF-8 compatibility
    writer = csv.writer(output)
    writer.writerow(
        ["Дата", "Клиент", "Услуга", "Сумма (руб)", "Способ оплаты", "Статус", "Чек"]
    )

    for item in items:
        created = item.get("created_at")
        date_str = created.strftime("%d.%m.%Y %H:%M") if created else ""
        writer.writerow([
            date_str,
            item.get("client_name") or "-",
            item.get("service_name") or "-",
            f"{item['amount'] / 100:.2f}",
            method_labels.get(item.get("payment_method") or "", item.get("payment_method") or "-"),
            status_labels.get(item.get("status", ""), item.get("status", "")),
            receipt_labels.get(item.get("receipt_status", ""), item.get("receipt_status", "")),
        ])

    output.seek(0)
    filename = f"payments_{date_from or 'all'}_{date_to or 'all'}.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/{payment_id}/confirm", response_model=PaymentRead)
async def confirm_requisites_payment(
    payment_id: uuid.UUID,
    data: PaymentConfirm,
    master: Annotated[Master, Depends(get_current_master)],
    db: Annotated[AsyncSession, Depends(get_db_with_rls)],
):
    """Confirm a pending requisites payment: master marks as paid."""
    payment = await PaymentService.confirm_requisites_payment(
        db=db,
        master=master,
        payment_id=payment_id,
        payment_method=data.payment_method,
    )
    return _payment_to_read(payment)


@router.post("/{payment_id}/cancel", response_model=PaymentRead)
async def cancel_payment(
    payment_id: uuid.UUID,
    master: Annotated[Master, Depends(get_current_master)],
    db: Annotated[AsyncSession, Depends(get_db_with_rls)],
):
    """Cancel a payment."""
    payment = await PaymentService.cancel_payment(
        db=db,
        master=master,
        payment_id=payment_id,
    )
    return _payment_to_read(payment)


@router.get("/history", response_model=PaymentListResponse)
async def get_payment_history(
    master: Annotated[Master, Depends(get_current_master)],
    db: Annotated[AsyncSession, Depends(get_db_with_rls)],
    status_filter: str | None = Query(default=None, alias="status"),
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    payment_method: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    """List payments with optional filters and pagination."""
    items, total, total_revenue = await PaymentService.get_payment_history(
        db=db,
        master_id=master.id,
        status_filter=status_filter,
        date_from=date_from,
        date_to=date_to,
        payment_method=payment_method,
        limit=limit,
        offset=offset,
    )
    return PaymentListResponse(
        items=[PaymentRead(**item) for item in items],
        total=total,
        total_revenue=total_revenue,
    )


@router.get("/{payment_id}/receipt-data", response_model=ManualReceiptData)
async def get_receipt_data(
    payment_id: uuid.UUID,
    master: Annotated[Master, Depends(get_current_master)],
    db: Annotated[AsyncSession, Depends(get_db_with_rls)],
):
    """Get pre-formatted receipt data for manual entry in 'Moy Nalog'."""
    from sqlalchemy import and_, select

    from app.models.payment import Payment

    result = await db.execute(
        select(Payment).where(
            and_(
                Payment.id == payment_id,
                Payment.master_id == master.id,
            )
        )
    )
    payment = result.scalar_one_or_none()

    if payment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found",
        )

    if not payment.receipt_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No receipt data available for this payment",
        )

    receipt = json.loads(payment.receipt_data)
    return ManualReceiptData(**receipt)
