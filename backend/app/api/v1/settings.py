"""Master settings GET/PUT endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_master, get_db_with_rls
from app.models.master import Master
from app.schemas.settings import MasterSettings, MasterSettingsUpdate

router = APIRouter()


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
