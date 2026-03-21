"""Reviews API: master-authenticated list + reply endpoints."""

import uuid
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.dependencies import get_current_master, get_db
from app.models.booking import Booking
from app.models.master import Master
from app.models.review import Review
from app.schemas.review import (
    ReviewAdminRead,
    ReviewReplyRequest,
    ReviewsListResponse,
)

router = APIRouter()


def _review_to_admin_read(review: Review) -> ReviewAdminRead:
    """Convert Review model to ReviewAdminRead schema."""
    client_name = ""
    client_phone = ""
    service_name = ""

    if review.client:
        client_name = review.client.name
        client_phone = review.client.phone

    if review.booking and review.booking.service:
        service_name = review.booking.service.name

    return ReviewAdminRead(
        id=review.id,
        booking_id=review.booking_id,
        rating=review.rating,
        text=review.text,
        client_name=client_name,
        client_phone=client_phone,
        service_name=service_name,
        master_reply=review.master_reply,
        master_replied_at=review.master_replied_at,
        status=review.status,
        created_at=review.created_at,
    )


@router.get("", response_model=ReviewsListResponse)
async def list_reviews(
    master: Annotated[Master, Depends(get_current_master)],
    db: Annotated[AsyncSession, Depends(get_db)],
    status_filter: str | None = Query(default=None, alias="status"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
):
    """List master's reviews (excluding request_sent sentinels)."""
    base_filter = [
        Review.master_id == master.id,
        Review.status != "request_sent",
    ]

    if status_filter and status_filter != "all":
        base_filter.append(Review.status == status_filter)

    # Count total
    count_q = select(func.count()).select_from(Review).where(*base_filter)
    total = (await db.execute(count_q)).scalar() or 0

    # Fetch paginated reviews with relationships
    offset = (page - 1) * page_size
    q = (
        select(Review)
        .where(*base_filter)
        .options(
            selectinload(Review.client),
            selectinload(Review.booking).selectinload(Booking.service),
        )
        .order_by(Review.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    result = await db.execute(q)
    reviews = result.scalars().all()

    return ReviewsListResponse(
        reviews=[_review_to_admin_read(r) for r in reviews],
        total=total,
    )


@router.put("/{review_id}/reply", response_model=ReviewAdminRead)
async def reply_to_review(
    review_id: uuid.UUID,
    body: ReviewReplyRequest,
    master: Annotated[Master, Depends(get_current_master)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Master replies to a review, which sets status to published."""
    q = (
        select(Review)
        .where(Review.id == review_id)
        .options(
            selectinload(Review.client),
            selectinload(Review.booking).selectinload(Booking.service),
        )
    )
    result = await db.execute(q)
    review = result.scalar_one_or_none()

    if review is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found",
        )

    # Security: master can only reply to own reviews
    if review.master_id != master.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not your review",
        )

    # Don't allow replying to request_sent sentinels
    if review.rating == 0 or review.status == "request_sent":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot reply to a review request",
        )

    review.master_reply = body.reply_text
    review.master_replied_at = datetime.now(tz=UTC)
    review.status = "published"

    await db.flush()
    await db.refresh(review)

    return _review_to_admin_read(review)
