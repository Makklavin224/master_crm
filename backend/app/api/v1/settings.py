"""Master settings GET/PUT endpoints + payment settings."""

from typing import Annotated

from fastapi import APIRouter, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_master, get_db_with_rls
from app.models.master import Master
from app.schemas.settings import (
    MasterSettings,
    MasterSettingsUpdate,
    PaymentSettings,
    PaymentSettingsUpdate,
    RobokassaSetup,
)

router = APIRouter()


# --- Booking settings ---


@router.get("", response_model=MasterSettings)
async def get_settings(
    master: Annotated[Master, Depends(get_current_master)],
):
    """Read master's booking settings."""
    return MasterSettings(
        buffer_minutes=master.buffer_minutes,
        cancellation_deadline_hours=master.cancellation_deadline_hours,
        slot_interval_minutes=master.slot_interval_minutes,
    )


@router.put("", response_model=MasterSettings)
async def update_settings(
    data: MasterSettingsUpdate,
    master: Annotated[Master, Depends(get_current_master)],
    db: Annotated[AsyncSession, Depends(get_db_with_rls)],
):
    """Update master's booking settings (partial update)."""
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(master, field, value)

    await db.flush()
    await db.refresh(master)

    return MasterSettings(
        buffer_minutes=master.buffer_minutes,
        cancellation_deadline_hours=master.cancellation_deadline_hours,
        slot_interval_minutes=master.slot_interval_minutes,
    )


# --- Payment settings ---


def _build_payment_settings(master: Master) -> PaymentSettings:
    """Build PaymentSettings from master model."""
    return PaymentSettings(
        card_number=master.card_number,
        sbp_phone=master.sbp_phone,
        bank_name=master.bank_name,
        has_robokassa=master.robokassa_merchant_login is not None,
        robokassa_is_test=master.robokassa_is_test,
        robokassa_hash_algorithm=master.robokassa_hash_algorithm,
        fiscalization_level=master.fiscalization_level,
        has_seen_grey_warning=master.has_seen_grey_warning,
        receipt_sno=master.receipt_sno,
    )


@router.get("/payment", response_model=PaymentSettings)
async def get_payment_settings(
    master: Annotated[Master, Depends(get_current_master)],
):
    """Read master's payment configuration."""
    return _build_payment_settings(master)


@router.put("/payment", response_model=PaymentSettings)
async def update_payment_settings(
    data: PaymentSettingsUpdate,
    master: Annotated[Master, Depends(get_current_master)],
    db: Annotated[AsyncSession, Depends(get_db_with_rls)],
):
    """Update master's payment requisites and fiscalization settings."""
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(master, field, value)

    await db.flush()
    await db.refresh(master)

    return _build_payment_settings(master)


@router.post("/payment/robokassa", response_model=PaymentSettings)
async def setup_robokassa(
    data: RobokassaSetup,
    master: Annotated[Master, Depends(get_current_master)],
    db: Annotated[AsyncSession, Depends(get_db_with_rls)],
):
    """Connect Robokassa credentials (passwords encrypted at rest)."""
    from app.services.encryption_service import encrypt_value

    master.robokassa_merchant_login = data.merchant_login
    master.robokassa_password1_encrypted = encrypt_value(data.password1)
    master.robokassa_password2_encrypted = encrypt_value(data.password2)
    master.robokassa_is_test = data.is_test
    master.robokassa_hash_algorithm = data.hash_algorithm

    await db.flush()
    await db.refresh(master)

    return _build_payment_settings(master)


@router.delete("/payment/robokassa", response_model=PaymentSettings)
async def disconnect_robokassa(
    master: Annotated[Master, Depends(get_current_master)],
    db: Annotated[AsyncSession, Depends(get_db_with_rls)],
):
    """Disconnect Robokassa: clear all credentials."""
    master.robokassa_merchant_login = None
    master.robokassa_password1_encrypted = None
    master.robokassa_password2_encrypted = None
    master.robokassa_is_test = False
    master.robokassa_hash_algorithm = "sha256"

    await db.flush()
    await db.refresh(master)

    return _build_payment_settings(master)


@router.post("/payment/grey-warning-seen", status_code=204)
async def mark_grey_warning_seen(
    master: Annotated[Master, Depends(get_current_master)],
    db: Annotated[AsyncSession, Depends(get_db_with_rls)],
):
    """Mark that master has seen the grey/no-receipts warning."""
    master.has_seen_grey_warning = True
    await db.flush()
    return Response(status_code=204)
