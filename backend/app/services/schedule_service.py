"""Schedule service: slot calculation algorithm."""

from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.booking import Booking
from app.models.schedule import MasterSchedule, ScheduleException


async def get_available_slots(
    db: AsyncSession,
    master_id,
    target_date: date,
    service_duration_minutes: int,
    buffer_minutes: int = 0,
    slot_interval_minutes: int = 30,
    master_timezone: str = "Europe/Moscow",
) -> list[time]:
    """
    Calculate available booking slots for a given master, date, and service duration.

    Returns a list of start times (in master's local timezone) that are genuinely free.

    Algorithm:
    1. Check for schedule exceptions (day off or custom hours).
    2. Fall back to weekly schedule if no exception.
    3. Generate candidate slots at interval steps.
    4. Filter out slots overlapping breaks or existing bookings.
    """
    tz = ZoneInfo(master_timezone)

    # 1. Check schedule exceptions for this date
    exc_result = await db.execute(
        select(ScheduleException).where(
            and_(
                ScheduleException.master_id == master_id,
                ScheduleException.exception_date == target_date,
            )
        )
    )
    exception = exc_result.scalar_one_or_none()

    if exception is not None:
        if exception.is_day_off:
            return []
        # Custom hours from exception
        if exception.start_time is not None and exception.end_time is not None:
            work_start = exception.start_time
            work_end = exception.end_time
            break_start = None
            break_end = None
        else:
            # Exception exists but no custom hours -- treat as day off
            return []
    else:
        # 2. Fall back to weekly schedule
        day_of_week = target_date.weekday()  # 0=Monday, 6=Sunday
        sched_result = await db.execute(
            select(MasterSchedule).where(
                and_(
                    MasterSchedule.master_id == master_id,
                    MasterSchedule.day_of_week == day_of_week,
                )
            )
        )
        schedule = sched_result.scalar_one_or_none()

        if schedule is None or not schedule.is_working:
            return []

        work_start = schedule.start_time
        work_end = schedule.end_time
        break_start = schedule.break_start
        break_end = schedule.break_end

    # 3. Query existing bookings for this master on this date
    day_start_dt = datetime.combine(target_date, time.min, tzinfo=tz)
    day_end_dt = datetime.combine(target_date, time.max, tzinfo=tz)

    bookings_result = await db.execute(
        select(Booking).where(
            and_(
                Booking.master_id == master_id,
                Booking.starts_at >= day_start_dt,
                Booking.starts_at < day_end_dt,
                Booking.status.in_(["confirmed", "pending"]),
            )
        )
    )
    existing_bookings = bookings_result.scalars().all()

    # Convert bookings to local time ranges
    booked_ranges = []
    for bk in existing_bookings:
        bk_start = bk.starts_at.astimezone(tz).time()
        bk_end = bk.ends_at.astimezone(tz).time()
        booked_ranges.append((bk_start, bk_end))

    # 4. Generate candidate slots
    total_slot_minutes = service_duration_minutes + buffer_minutes
    slots = []

    # Convert to minutes from midnight for easier arithmetic
    work_start_min = work_start.hour * 60 + work_start.minute
    work_end_min = work_end.hour * 60 + work_end.minute

    current_min = work_start_min
    while current_min + service_duration_minutes <= work_end_min:
        slot_start = time(current_min // 60, current_min % 60)
        slot_end_min = current_min + service_duration_minutes
        slot_end = time(slot_end_min // 60, slot_end_min % 60)

        # Check break overlap
        if break_start is not None and break_end is not None:
            if _times_overlap(slot_start, slot_end, break_start, break_end):
                current_min += slot_interval_minutes
                continue

        # Check booking overlap
        has_conflict = False
        for bk_start, bk_end in booked_ranges:
            if _times_overlap(slot_start, slot_end, bk_start, bk_end):
                has_conflict = True
                break

        if not has_conflict:
            slots.append(slot_start)

        current_min += slot_interval_minutes

    return slots


def _times_overlap(
    start1: time, end1: time, start2: time, end2: time
) -> bool:
    """Check if two time ranges overlap. Assumes all ranges are within the same day."""
    return start1 < end2 and start2 < end1
