"""Schedule management endpoints (auth required)."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_master, get_db_with_rls
from app.models.master import Master
from app.models.schedule import MasterSchedule, ScheduleException
from app.schemas.schedule import (
    ScheduleDayRead,
    ScheduleExceptionCreate,
    ScheduleExceptionRead,
    ScheduleTemplate,
)

router = APIRouter()


@router.get("", response_model=list[ScheduleDayRead])
async def get_schedule(
    master: Annotated[Master, Depends(get_current_master)],
    db: Annotated[AsyncSession, Depends(get_db_with_rls)],
):
    """Get the 7-day weekly schedule template for the authenticated master."""
    result = await db.execute(
        select(MasterSchedule).order_by(MasterSchedule.day_of_week)
    )
    return result.scalars().all()


@router.put("", response_model=list[ScheduleDayRead])
async def upsert_schedule(
    template: ScheduleTemplate,
    master: Annotated[Master, Depends(get_current_master)],
    db: Annotated[AsyncSession, Depends(get_db_with_rls)],
):
    """Upsert the 7-day weekly schedule (delete existing + insert new)."""
    # Delete existing schedule entries (RLS-scoped)
    await db.execute(delete(MasterSchedule))

    # Insert new entries
    for entry in template.days:
        schedule = MasterSchedule(
            master_id=master.id,
            day_of_week=entry.day_of_week,
            start_time=entry.start_time,
            end_time=entry.end_time,
            break_start=entry.break_start,
            break_end=entry.break_end,
            is_working=entry.is_working,
        )
        db.add(schedule)

    await db.flush()

    result = await db.execute(
        select(MasterSchedule).order_by(MasterSchedule.day_of_week)
    )
    return result.scalars().all()


@router.get("/exceptions", response_model=list[ScheduleExceptionRead])
async def list_exceptions(
    master: Annotated[Master, Depends(get_current_master)],
    db: Annotated[AsyncSession, Depends(get_db_with_rls)],
):
    """List schedule exceptions for the authenticated master."""
    result = await db.execute(
        select(ScheduleException).order_by(ScheduleException.exception_date)
    )
    return result.scalars().all()


@router.post("/exceptions", response_model=ScheduleExceptionRead, status_code=201)
async def create_exception(
    data: ScheduleExceptionCreate,
    master: Annotated[Master, Depends(get_current_master)],
    db: Annotated[AsyncSession, Depends(get_db_with_rls)],
):
    """Create a schedule exception (day off or custom hours)."""
    exception = ScheduleException(
        master_id=master.id,
        exception_date=data.exception_date,
        is_day_off=data.is_day_off,
        start_time=data.start_time,
        end_time=data.end_time,
        reason=data.reason,
    )
    db.add(exception)
    await db.flush()
    await db.refresh(exception)
    return exception


@router.delete("/exceptions/{exception_id}", status_code=204)
async def delete_exception(
    exception_id: uuid.UUID,
    master: Annotated[Master, Depends(get_current_master)],
    db: Annotated[AsyncSession, Depends(get_db_with_rls)],
):
    """Delete a schedule exception."""
    result = await db.execute(
        select(ScheduleException).where(ScheduleException.id == exception_id)
    )
    exception = result.scalar_one_or_none()
    if exception is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Schedule exception not found",
        )
    await db.delete(exception)
    await db.flush()
