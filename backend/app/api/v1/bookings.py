"""Booking CRUD endpoints."""

import uuid
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_master, get_db, get_db_with_rls, get_optional_master
from app.models.master import Master
from app.schemas.booking import (
    BookingCancel,
    BookingCreate,
    BookingListResponse,
    BookingRead,
    BookingReschedule,
    ManualBookingCreate,
)
from app.services.booking_service import (
    cancel_booking,
    complete_booking,
    create_booking,
    create_manual_booking,
    get_master_bookings,
    mark_no_show,
    reschedule_booking,
)

router = APIRouter()


def _booking_to_read(booking) -> BookingRead:
    """Convert Booking model to BookingRead schema with nested fields."""
    return BookingRead(
        id=booking.id,
        master_id=booking.master_id,
        client_id=booking.client_id,
        service_id=booking.service_id,
        starts_at=booking.starts_at,
        ends_at=booking.ends_at,
        status=booking.status,
        source_platform=booking.source_platform,
        notes=booking.notes,
        created_at=booking.created_at,
        service_name=booking.service.name if booking.service else None,
        client_name=booking.client.name if booking.client else None,
        client_phone=booking.client.phone if booking.client else None,
    )


@router.post("", response_model=BookingRead, status_code=201)
async def create_booking_endpoint(
    data: BookingCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Create a new booking (public -- will be secured in Plan 02)."""
    booking = await create_booking(
        db=db,
        master_id=data.master_id,
        service_id=data.service_id,
        starts_at=data.starts_at,
        client_name=data.client_name,
        client_phone=data.client_phone,
        source_platform=data.source_platform,
        platform_user_id=data.platform_user_id,
    )
    return _booking_to_read(booking)


@router.get("", response_model=BookingListResponse)
async def list_bookings(
    master: Annotated[Master, Depends(get_current_master)],
    db: Annotated[AsyncSession, Depends(get_db_with_rls)],
    date_from: datetime | None = Query(default=None),
    date_to: datetime | None = Query(default=None),
    status: str | None = Query(default=None),
):
    """List bookings for the authenticated master with optional filters."""
    bookings = await get_master_bookings(
        db=db,
        master_id=master.id,
        date_from=date_from,
        date_to=date_to,
        booking_status=status,
    )
    return BookingListResponse(
        bookings=[_booking_to_read(b) for b in bookings],
        total=len(bookings),
    )


@router.get("/{booking_id}", response_model=BookingRead)
async def get_booking(
    booking_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    master: Annotated[Master | None, Depends(get_optional_master)] = None,
):
    """Get a single booking by ID."""
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload

    from app.models.booking import Booking

    result = await db.execute(
        select(Booking)
        .where(Booking.id == booking_id)
        .options(selectinload(Booking.client), selectinload(Booking.service))
    )
    booking = result.scalar_one_or_none()
    if booking is None:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Booking not found")
    return _booking_to_read(booking)


@router.post("/manual", response_model=BookingRead, status_code=201)
async def create_manual_booking_endpoint(
    data: ManualBookingCreate,
    master: Annotated[Master, Depends(get_current_master)],
    db: Annotated[AsyncSession, Depends(get_db_with_rls)],
):
    """Create a booking manually (master-only)."""
    booking = await create_manual_booking(
        db=db,
        master_id=master.id,
        service_id=data.service_id,
        starts_at=data.starts_at,
        client_name=data.client_name,
        client_phone=data.client_phone,
        notes=data.notes,
    )
    return _booking_to_read(booking)


@router.put("/{booking_id}/cancel", response_model=BookingRead)
async def cancel_booking_endpoint(
    booking_id: uuid.UUID,
    data: BookingCancel,
    db: Annotated[AsyncSession, Depends(get_db)],
    master: Annotated[Master | None, Depends(get_optional_master)] = None,
):
    """Cancel a booking. Master or client auth determines deadline enforcement."""
    if master is not None:
        cancelled_by = "master"
        deadline_hours = None  # No deadline for master
    else:
        cancelled_by = "client"
        # Look up master's cancellation deadline from the booking
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload

        from app.models.booking import Booking

        bk_result = await db.execute(
            select(Booking)
            .where(Booking.id == booking_id)
            .options(selectinload(Booking.master))
        )
        bk = bk_result.scalar_one_or_none()
        deadline_hours = (
            bk.master.cancellation_deadline_hours if bk and bk.master else 24
        )

    booking = await cancel_booking(
        db=db,
        booking_id=booking_id,
        cancelled_by=cancelled_by,
        cancellation_deadline_hours=deadline_hours,
    )
    return _booking_to_read(booking)


@router.put("/{booking_id}/complete", response_model=BookingRead)
async def complete_booking_endpoint(
    booking_id: uuid.UUID,
    master: Annotated[Master, Depends(get_current_master)],
    db: Annotated[AsyncSession, Depends(get_db_with_rls)],
):
    """Mark a booking as completed (master-only)."""
    booking = await complete_booking(db=db, booking_id=booking_id, master_id=master.id)
    return _booking_to_read(booking)


@router.put("/{booking_id}/no_show", response_model=BookingRead)
async def mark_no_show_endpoint(
    booking_id: uuid.UUID,
    master: Annotated[Master, Depends(get_current_master)],
    db: Annotated[AsyncSession, Depends(get_db_with_rls)],
):
    """Mark a booking as no-show (master-only)."""
    booking = await mark_no_show(db=db, booking_id=booking_id, master_id=master.id)
    return _booking_to_read(booking)


@router.put("/{booking_id}/reschedule", response_model=BookingRead)
async def reschedule_booking_endpoint(
    booking_id: uuid.UUID,
    data: BookingReschedule,
    db: Annotated[AsyncSession, Depends(get_db)],
    master: Annotated[Master | None, Depends(get_optional_master)] = None,
):
    """Reschedule a booking. Master or client auth determines deadline enforcement."""
    if master is not None:
        rescheduled_by = "master"
        deadline_hours = None
    else:
        rescheduled_by = "client"
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload

        from app.models.booking import Booking

        bk_result = await db.execute(
            select(Booking)
            .where(Booking.id == booking_id)
            .options(selectinload(Booking.master))
        )
        bk = bk_result.scalar_one_or_none()
        deadline_hours = (
            bk.master.cancellation_deadline_hours if bk and bk.master else 24
        )

    booking = await reschedule_booking(
        db=db,
        booking_id=booking_id,
        new_starts_at=data.new_starts_at,
        rescheduled_by=rescheduled_by,
        cancellation_deadline_hours=deadline_hours,
    )
    return _booking_to_read(booking)
