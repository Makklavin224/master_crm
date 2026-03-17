"""Public master endpoints (no auth required)."""

import uuid
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.models.master import Master
from app.models.service import Service
from app.schemas.service import ServiceRead
from app.schemas.slot import AvailableSlot, AvailableSlotsResponse
from app.services.schedule_service import get_available_slots

router = APIRouter()


@router.get("/{master_id}/services", response_model=list[ServiceRead])
async def list_master_services_public(
    master_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """List active services for a master (public, no auth required)."""
    result = await db.execute(
        select(Service)
        .where(Service.master_id == master_id, Service.is_active.is_(True))
        .order_by(Service.sort_order)
    )
    return result.scalars().all()


@router.get("/{master_id}/slots", response_model=AvailableSlotsResponse)
async def get_slots(
    master_id: uuid.UUID,
    date: date = Query(..., description="Date to check for available slots"),
    service_id: uuid.UUID = Query(
        ..., description="Service ID to calculate slot duration"
    ),
    db: AsyncSession = Depends(get_db),
):
    """Get available booking slots for a master on a given date (public, no auth)."""
    # Look up service to get duration
    service_result = await db.execute(
        select(Service).where(
            and_(
                Service.id == service_id,
                Service.master_id == master_id,
                Service.is_active.is_(True),
            )
        )
    )
    service = service_result.scalar_one_or_none()
    if service is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Service not found"
        )

    # Look up master settings
    master_result = await db.execute(select(Master).where(Master.id == master_id))
    master = master_result.scalar_one_or_none()
    if master is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Master not found"
        )

    slots = await get_available_slots(
        db=db,
        master_id=master_id,
        target_date=date,
        service_duration_minutes=service.duration_minutes,
        buffer_minutes=master.buffer_minutes,
        slot_interval_minutes=master.slot_interval_minutes,
        master_timezone=master.timezone,
    )

    return AvailableSlotsResponse(
        date=date,
        slots=[AvailableSlot(time=s) for s in slots],
    )
