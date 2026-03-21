"""Auto-publish service: APScheduler-based polling for stale pending_reply reviews.

Polls every hour, finds reviews with status='pending_reply' older than 7 days,
and auto-publishes them by setting status='published'.
"""

import logging
from datetime import datetime, timedelta, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import and_, select, update

from app.core.database import async_session_factory
from app.models.review import Review

logger = logging.getLogger(__name__)

# Module-level scheduler singleton
auto_publish_scheduler = AsyncIOScheduler(timezone="UTC")


async def process_auto_publish_reviews() -> None:
    """Poll for stale pending_reply reviews and auto-publish them.

    Query reviews WHERE status='pending_reply' AND created_at <= now - 7 days.
    Update status to 'published' in batch.
    """
    try:
        async with async_session_factory() as session:
            now = datetime.now(timezone.utc)
            seven_days_ago = now - timedelta(days=7)

            # Find stale pending_reply reviews
            result = await session.execute(
                select(Review).where(
                    and_(
                        Review.status == "pending_reply",
                        Review.created_at <= seven_days_ago,
                    )
                )
            )
            reviews = result.scalars().all()

            if not reviews:
                return

            review_ids = [r.id for r in reviews]

            # Batch update to published
            await session.execute(
                update(Review)
                .where(Review.id.in_(review_ids))
                .values(status="published", updated_at=now)
            )

            await session.commit()

            logger.info(
                "Auto-published %d stale pending_reply reviews",
                len(review_ids),
            )

    except Exception:
        logger.exception("Error in process_auto_publish_reviews")


# Register the polling job
auto_publish_scheduler.add_job(
    process_auto_publish_reviews,
    "interval",
    hours=1,
    id="auto_publish_poll",
    replace_existing=True,
    misfire_grace_time=3600,
)
