"""Client cabinet endpoints: bookings list and review submission.

GET  /bookings  - All client bookings across all masters (upcoming + past)
POST /reviews   - Submit review for a completed booking
"""

from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.dependencies import get_current_client, get_db
from app.models.booking import Booking
from app.models.client import Client
from app.models.review import Review
from app.schemas.client import (
    ClientBookingRead,
    ClientBookingsResponse,
    ReviewCreate,
    ReviewCreateResponse,
)

router = APIRouter()


@router.get("/bookings", response_model=ClientBookingsResponse)
async def get_client_bookings(
    client: Annotated[Client, Depends(get_current_client)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ClientBookingsResponse:
    """Return all bookings for the authenticated client, split into upcoming and past."""
    now = datetime.now(timezone.utc)

    result = await db.execute(
        select(Booking)
        .where(Booking.client_id == client.id)
        .options(
            selectinload(Booking.master),
            selectinload(Booking.service),
        )
        .order_by(Booking.starts_at.desc())
    )
    bookings = result.scalars().all()

    upcoming: list[ClientBookingRead] = []
    past: list[ClientBookingRead] = []

    for b in bookings:
        item = ClientBookingRead(
            id=b.id,
            master_id=b.master_id,
            master_name=b.master.name,
            service_id=b.service_id,
            service_name=b.service.name,
            starts_at=b.starts_at,
            ends_at=b.ends_at,
            status=b.status,
            source_platform=b.source_platform,
            master_username=b.master.username,
        )

        is_upcoming = (
            b.starts_at > now
            and b.status == "confirmed"
        )
        if is_upcoming:
            upcoming.append(item)
        else:
            past.append(item)

    # Upcoming sorted by starts_at ASC (soonest first)
    upcoming.sort(key=lambda x: x.starts_at)
    # Past already sorted DESC from query

    return ClientBookingsResponse(upcoming=upcoming, past=past)


@router.post("/reviews", response_model=ReviewCreateResponse, status_code=201)
async def create_client_review(
    body: ReviewCreate,
    client: Annotated[Client, Depends(get_current_client)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ReviewCreateResponse:
    """Submit a review for a completed booking owned by the client."""
    now = datetime.now(timezone.utc)

    # Validate booking exists
    result = await db.execute(
        select(Booking).where(Booking.id == body.booking_id)
    )
    booking = result.scalar_one_or_none()
    if not booking:
        raise HTTPException(status_code=404, detail="Запись не найдена")

    # Validate ownership
    if booking.client_id != client.id:
        raise HTTPException(status_code=403, detail="Это не ваша запись")

    # Validate completed status
    if booking.status != "completed":
        raise HTTPException(
            status_code=400,
            detail="Отзыв можно оставить только после завершённого визита",
        )

    # Check no existing review for this booking
    result = await db.execute(
        select(Review).where(Review.booking_id == body.booking_id)
    )
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=409,
            detail="Вы уже оставили отзыв на этот визит",
        )

    # Validate within 30-day window
    if booking.ends_at < now - timedelta(days=30):
        raise HTTPException(
            status_code=400,
            detail="Срок для отзыва истёк (30 дней)",
        )

    # Determine review status: rating >= 3 auto-publish, else pending_reply
    review_status = "published" if body.rating >= 3 else "pending_reply"

    review = Review(
        booking_id=body.booking_id,
        master_id=booking.master_id,
        client_id=client.id,
        rating=body.rating,
        text=body.text,
        status=review_status,
    )
    db.add(review)
    await db.flush()
    await db.refresh(review)

    return ReviewCreateResponse(
        id=review.id,
        rating=review.rating,
        text=review.text,
        created_at=review.created_at,
    )
