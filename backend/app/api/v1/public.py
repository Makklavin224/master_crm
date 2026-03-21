"""Public master page endpoints (no auth required).

All endpoints accept both username strings and UUID strings as the
``identifier`` path parameter.
"""

import uuid
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.dependencies import get_db
from app.models.master import Master
from app.models.review import Review
from app.models.service import Service
from app.schemas.master import MasterPublicProfile
from app.schemas.review import ReviewRead
from app.schemas.service import ServiceRead
from app.schemas.slot import AvailableSlot, AvailableSlotsResponse
from app.services.schedule_service import get_available_slots

router = APIRouter()


async def _get_master_by_identifier(
    identifier: str, db: AsyncSession
) -> Master:
    """Resolve a master by username or UUID.  Raises 404 if not found or inactive."""
    # Try UUID first
    try:
        master_uuid = uuid.UUID(identifier)
        result = await db.execute(
            select(Master).where(Master.id == master_uuid)
        )
    except ValueError:
        # Not a valid UUID -- treat as username
        result = await db.execute(
            select(Master).where(Master.username == identifier)
        )

    master = result.scalar_one_or_none()
    if master is None or not master.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Master not found"
        )
    return master


@router.get("/{identifier}/profile", response_model=MasterPublicProfile)
async def get_master_profile(
    identifier: str,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Return a master's public profile with computed rating stats."""
    master = await _get_master_by_identifier(identifier, db)

    # Compute avg_rating and review_count from published reviews
    stats = await db.execute(
        select(
            func.avg(Review.rating).label("avg_rating"),
            func.count(Review.id).label("review_count"),
        ).where(
            and_(
                Review.master_id == master.id,
                Review.status == "published",
            )
        )
    )
    row = stats.one()
    avg_rating = float(round(row.avg_rating, 2)) if row.avg_rating is not None else None

    return MasterPublicProfile(
        id=master.id,
        name=master.name,
        username=master.username,
        specialization=master.specialization,
        city=master.city,
        avatar_path=master.avatar_path,
        instagram_url=master.instagram_url,
        avg_rating=avg_rating,
        review_count=row.review_count,
    )


@router.get("/{identifier}/services", response_model=list[ServiceRead])
async def list_master_services(
    identifier: str,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """List active services for a master (public, no auth required)."""
    master = await _get_master_by_identifier(identifier, db)

    result = await db.execute(
        select(Service)
        .where(
            and_(
                Service.master_id == master.id,
                Service.is_active.is_(True),
            )
        )
        .order_by(Service.sort_order)
    )
    return result.scalars().all()


@router.get("/{identifier}/slots", response_model=AvailableSlotsResponse)
async def get_master_slots(
    identifier: str,
    date: date = Query(..., description="Date to check for available slots"),
    service_id: uuid.UUID = Query(
        ..., description="Service ID to calculate slot duration"
    ),
    db: AsyncSession = Depends(get_db),
):
    """Get available booking slots for a master on a given date (public, no auth)."""
    master = await _get_master_by_identifier(identifier, db)

    # Validate service belongs to master and is active
    service_result = await db.execute(
        select(Service).where(
            and_(
                Service.id == service_id,
                Service.master_id == master.id,
                Service.is_active.is_(True),
            )
        )
    )
    service = service_result.scalar_one_or_none()
    if service is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Service not found"
        )

    slots = await get_available_slots(
        db=db,
        master_id=master.id,
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


@router.get("/{identifier}/reviews", response_model=list[ReviewRead])
async def list_master_reviews(
    identifier: str,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """List published reviews for a master (public, no auth required)."""
    master = await _get_master_by_identifier(identifier, db)

    result = await db.execute(
        select(Review)
        .where(
            and_(
                Review.master_id == master.id,
                Review.status == "published",
            )
        )
        .options(selectinload(Review.client))
        .order_by(Review.created_at.desc())
        .limit(50)
    )
    reviews = result.scalars().all()

    return [
        ReviewRead(
            id=r.id,
            rating=r.rating,
            text=r.text,
            client_name=r.client.name,
            master_reply=r.master_reply,
            master_replied_at=r.master_replied_at,
            created_at=r.created_at,
        )
        for r in reviews
    ]
