"""Review request service: APScheduler-based polling for sending review requests.

Polls every 10 minutes, finds completed bookings 2h+ old with no Review row,
sends review request via bot with star buttons, creates sentinel Review row
(rating=0, status=request_sent) to prevent re-sending.
"""

import logging
from datetime import datetime, timedelta, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.bots.common.notification import notification_service
from app.core.database import async_session_factory
from app.models.booking import Booking
from app.models.client import ClientPlatform
from app.models.master import Master
from app.models.review import Review
from app.models.service import Service

logger = logging.getLogger(__name__)

# Module-level scheduler singleton
review_request_scheduler = AsyncIOScheduler(timezone="UTC")


async def process_pending_review_requests() -> None:
    """Poll for completed bookings and send review requests to clients.

    Query bookings WHERE status='completed' AND ends_at between (now - 30d) and (now - 2h)
    AND no Review row exists for that booking_id.
    For each match: send review request via bot, create sentinel Review row.
    """
    try:
        async with async_session_factory() as session:
            now = datetime.now(timezone.utc)
            two_hours_ago = now - timedelta(hours=2)
            thirty_days_ago = now - timedelta(days=30)

            # Find completed bookings eligible for review request:
            # ended 2h+ ago but within 30-day window, with no existing Review
            existing_reviews = (
                select(Review.booking_id)
                .where(Review.booking_id.is_not(None))
                .scalar_subquery()
            )

            result = await session.execute(
                select(Booking)
                .where(
                    and_(
                        Booking.status == "completed",
                        Booking.ends_at <= two_hours_ago,
                        Booking.ends_at >= thirty_days_ago,
                        Booking.id.not_in(existing_reviews),
                    )
                )
            )
            bookings = result.scalars().all()

            if not bookings:
                return

            logger.info(
                "Found %d completed bookings eligible for review request",
                len(bookings),
            )

            for booking in bookings:
                try:
                    await _send_review_request(session, booking)
                except Exception:
                    logger.exception(
                        "Error sending review request for booking %s",
                        booking.id,
                    )

            await session.commit()

    except Exception:
        logger.exception("Error in process_pending_review_requests")


async def _send_review_request(
    session: AsyncSession,
    booking: Booking,
) -> None:
    """Send a review request for a single booking and create sentinel Review row."""
    # Find client's platform (prefer booking.source_platform, fallback to any)
    source_platform = booking.source_platform or "telegram"
    platform_result = await session.execute(
        select(ClientPlatform).where(
            and_(
                ClientPlatform.client_id == booking.client_id,
                ClientPlatform.platform == source_platform,
            )
        )
    )
    platform_record = platform_result.scalar_one_or_none()

    # Fallback: try any available platform
    if not platform_record:
        platform_result = await session.execute(
            select(ClientPlatform).where(
                ClientPlatform.client_id == booking.client_id,
            )
        )
        platform_record = platform_result.scalar_one_or_none()
        if platform_record:
            source_platform = platform_record.platform

    if not platform_record:
        logger.warning(
            "No platform found for client %s (booking %s), skipping review request",
            booking.client_id,
            booking.id,
        )
        return

    # Load master name
    master_result = await session.execute(
        select(Master).where(Master.id == booking.master_id)
    )
    master = master_result.scalar_one_or_none()
    master_name = master.name if master else "Мастер"

    # Load service name
    svc_result = await session.execute(
        select(Service).where(Service.id == booking.service_id)
    )
    service = svc_result.scalar_one_or_none()
    service_name = service.name if service else "Услуга"

    # Send the review request via bot
    success = await notification_service.send_review_request(
        platform=source_platform,
        platform_user_id=platform_record.platform_user_id,
        master_name=master_name,
        service_name=service_name,
        booking_id=str(booking.id),
    )

    if success:
        # Create sentinel Review row to prevent re-sending
        review = Review(
            booking_id=booking.id,
            master_id=booking.master_id,
            client_id=booking.client_id,
            rating=0,
            status="request_sent",
        )
        session.add(review)
        await session.flush()

        logger.info(
            "Sent review request for booking %s to client %s via %s",
            booking.id,
            booking.client_id,
            source_platform,
        )
    else:
        logger.warning(
            "Failed to send review request for booking %s",
            booking.id,
        )


# Register the polling job
review_request_scheduler.add_job(
    process_pending_review_requests,
    "interval",
    minutes=10,
    id="review_request_poll",
    replace_existing=True,
    misfire_grace_time=600,
)
