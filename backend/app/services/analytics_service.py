"""Analytics service: SQL aggregation queries for dashboard and report metrics."""

import uuid
from datetime import date, timedelta

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.analytics import (
    AnalyticsSummary,
    DailyBreakdownRow,
    RevenueChartPoint,
    TopServiceRow,
)


class AnalyticsService:
    """Compute analytics metrics from bookings, payments, schedules, and clients."""

    @staticmethod
    async def get_summary(
        db: AsyncSession,
        master_id: uuid.UUID,
        date_from: date,
        date_to: date,
    ) -> AnalyticsSummary:
        """Compute all summary metrics for a date range."""
        from app.models.booking import Booking
        from app.models.client import MasterClient
        from app.models.payment import Payment
        from app.models.schedule import MasterSchedule, ScheduleException

        # --- Revenue: SUM of paid payments in range ---
        revenue_q = select(
            func.coalesce(func.sum(Payment.amount), 0)
        ).where(
            and_(
                Payment.master_id == master_id,
                Payment.status == "paid",
                func.date(Payment.paid_at) >= date_from,
                func.date(Payment.paid_at) <= date_to,
            )
        )
        revenue_result = await db.execute(revenue_q)
        revenue = revenue_result.scalar_one()

        # --- Booking count: all non-cancelled bookings in range ---
        cancelled_statuses = ("cancelled_by_client", "cancelled_by_master")
        booking_count_q = select(func.count()).select_from(Booking).where(
            and_(
                Booking.master_id == master_id,
                func.date(Booking.starts_at) >= date_from,
                func.date(Booking.starts_at) <= date_to,
                Booking.status.notin_(cancelled_statuses),
            )
        )
        booking_count_result = await db.execute(booking_count_q)
        booking_count = booking_count_result.scalar_one()

        # --- Total bookings (all statuses) for rate calculations ---
        total_bookings_q = select(func.count()).select_from(Booking).where(
            and_(
                Booking.master_id == master_id,
                func.date(Booking.starts_at) >= date_from,
                func.date(Booking.starts_at) <= date_to,
            )
        )
        total_bookings_result = await db.execute(total_bookings_q)
        total_bookings = total_bookings_result.scalar_one()

        # --- Client count: distinct clients from bookings in range ---
        client_count_q = select(
            func.count(func.distinct(Booking.client_id))
        ).where(
            and_(
                Booking.master_id == master_id,
                func.date(Booking.starts_at) >= date_from,
                func.date(Booking.starts_at) <= date_to,
                Booking.status.notin_(cancelled_statuses),
            )
        )
        client_count_result = await db.execute(client_count_q)
        client_count = client_count_result.scalar_one()

        # --- New vs repeat clients ---
        # Get distinct client_ids from bookings in range
        clients_in_range_q = select(
            func.distinct(Booking.client_id)
        ).where(
            and_(
                Booking.master_id == master_id,
                func.date(Booking.starts_at) >= date_from,
                func.date(Booking.starts_at) <= date_to,
                Booking.status.notin_(cancelled_statuses),
            )
        )
        clients_in_range_result = await db.execute(clients_in_range_q)
        client_ids_in_range = [row[0] for row in clients_in_range_result.all()]

        new_clients = 0
        repeat_clients = 0
        if client_ids_in_range:
            # New: first_visit_at is within range
            new_q = select(func.count()).select_from(MasterClient).where(
                and_(
                    MasterClient.master_id == master_id,
                    MasterClient.client_id.in_(client_ids_in_range),
                    func.date(MasterClient.first_visit_at) >= date_from,
                    func.date(MasterClient.first_visit_at) <= date_to,
                )
            )
            new_result = await db.execute(new_q)
            new_clients = new_result.scalar_one()
            repeat_clients = len(client_ids_in_range) - new_clients

        # --- Utilization ---
        # Completed booking minutes in range
        completed_q = select(Booking.starts_at, Booking.ends_at).where(
            and_(
                Booking.master_id == master_id,
                func.date(Booking.starts_at) >= date_from,
                func.date(Booking.starts_at) <= date_to,
                Booking.status == "completed",
            )
        )
        completed_result = await db.execute(completed_q)
        completed_rows = completed_result.all()
        booked_minutes = sum(
            (row.ends_at - row.starts_at).total_seconds() / 60
            for row in completed_rows
        )

        # Scheduled working hours in range
        schedules_q = select(MasterSchedule).where(
            and_(
                MasterSchedule.master_id == master_id,
                MasterSchedule.is_working == True,  # noqa: E712
            )
        )
        schedules_result = await db.execute(schedules_q)
        schedules = {s.day_of_week: s for s in schedules_result.scalars().all()}

        exceptions_q = select(ScheduleException).where(
            and_(
                ScheduleException.master_id == master_id,
                ScheduleException.exception_date >= date_from,
                ScheduleException.exception_date <= date_to,
            )
        )
        exceptions_result = await db.execute(exceptions_q)
        exceptions = {
            e.exception_date: e for e in exceptions_result.scalars().all()
        }

        scheduled_minutes = _calc_scheduled_minutes(
            date_from, date_to, schedules, exceptions
        )

        utilization = (
            round(booked_minutes / scheduled_minutes * 100, 1)
            if scheduled_minutes > 0
            else 0.0
        )

        # --- Avg check ---
        paid_count_q = select(func.count()).select_from(Payment).where(
            and_(
                Payment.master_id == master_id,
                Payment.status == "paid",
                func.date(Payment.paid_at) >= date_from,
                func.date(Payment.paid_at) <= date_to,
            )
        )
        paid_count_result = await db.execute(paid_count_q)
        paid_count = paid_count_result.scalar_one()
        avg_check = int(revenue / paid_count) if paid_count > 0 else 0

        # --- Retention rate ---
        # Clients who visited before date_from
        prior_clients_q = select(func.count()).select_from(MasterClient).where(
            and_(
                MasterClient.master_id == master_id,
                func.date(MasterClient.first_visit_at) < date_from,
                MasterClient.visit_count > 0,
            )
        )
        prior_clients_result = await db.execute(prior_clients_q)
        prior_clients_count = prior_clients_result.scalar_one()

        retention_rate = 0.0
        if prior_clients_count > 0:
            # Of those prior clients, how many have a booking in range
            returning_q = select(func.count()).select_from(MasterClient).where(
                and_(
                    MasterClient.master_id == master_id,
                    func.date(MasterClient.first_visit_at) < date_from,
                    MasterClient.visit_count > 0,
                    MasterClient.client_id.in_(client_ids_in_range),
                )
            )
            returning_result = await db.execute(returning_q)
            returning_count = returning_result.scalar_one()
            retention_rate = round(
                returning_count / prior_clients_count * 100, 1
            )

        # --- Cancel rate ---
        cancel_count_q = select(func.count()).select_from(Booking).where(
            and_(
                Booking.master_id == master_id,
                func.date(Booking.starts_at) >= date_from,
                func.date(Booking.starts_at) <= date_to,
                Booking.status.in_(cancelled_statuses),
            )
        )
        cancel_count_result = await db.execute(cancel_count_q)
        cancel_count = cancel_count_result.scalar_one()
        cancel_rate = (
            round(cancel_count / total_bookings * 100, 1)
            if total_bookings > 0
            else 0.0
        )

        # --- No-show rate ---
        noshow_count_q = select(func.count()).select_from(Booking).where(
            and_(
                Booking.master_id == master_id,
                func.date(Booking.starts_at) >= date_from,
                func.date(Booking.starts_at) <= date_to,
                Booking.status == "no_show",
            )
        )
        noshow_count_result = await db.execute(noshow_count_q)
        noshow_count = noshow_count_result.scalar_one()
        noshow_rate = (
            round(noshow_count / total_bookings * 100, 1)
            if total_bookings > 0
            else 0.0
        )

        return AnalyticsSummary(
            revenue=revenue,
            booking_count=booking_count,
            client_count=client_count,
            new_clients=new_clients,
            repeat_clients=repeat_clients,
            utilization=utilization,
            avg_check=avg_check,
            retention_rate=retention_rate,
            cancel_rate=cancel_rate,
            noshow_rate=noshow_rate,
        )

    @staticmethod
    async def get_revenue_chart(
        db: AsyncSession,
        master_id: uuid.UUID,
        date_from: date,
        date_to: date,
    ) -> list[RevenueChartPoint]:
        """Return daily revenue points, filling gaps with zero."""
        from app.models.payment import Payment

        q = select(
            func.date(Payment.paid_at).label("day"),
            func.coalesce(func.sum(Payment.amount), 0).label("total"),
        ).where(
            and_(
                Payment.master_id == master_id,
                Payment.status == "paid",
                func.date(Payment.paid_at) >= date_from,
                func.date(Payment.paid_at) <= date_to,
            )
        ).group_by(
            func.date(Payment.paid_at)
        ).order_by(
            func.date(Payment.paid_at)
        )
        result = await db.execute(q)
        revenue_by_day = {row.day: int(row.total) for row in result.all()}

        # Fill gaps
        points: list[RevenueChartPoint] = []
        current = date_from
        while current <= date_to:
            points.append(
                RevenueChartPoint(
                    date=current.isoformat(),
                    revenue=revenue_by_day.get(current, 0),
                )
            )
            current += timedelta(days=1)

        return points

    @staticmethod
    async def get_top_services(
        db: AsyncSession,
        master_id: uuid.UUID,
        date_from: date,
        date_to: date,
    ) -> list[TopServiceRow]:
        """Return services ranked by revenue with counts and percentages."""
        from app.models.booking import Booking
        from app.models.payment import Payment
        from app.models.service import Service

        q = (
            select(
                Service.name.label("service_name"),
                func.count(Booking.id).label("booking_count"),
                func.coalesce(func.sum(Payment.amount), 0).label("revenue"),
            )
            .select_from(Booking)
            .join(Payment, Payment.booking_id == Booking.id)
            .join(Service, Service.id == Booking.service_id)
            .where(
                and_(
                    Booking.master_id == master_id,
                    Payment.status == "paid",
                    func.date(Booking.starts_at) >= date_from,
                    func.date(Booking.starts_at) <= date_to,
                )
            )
            .group_by(Service.name)
            .order_by(func.sum(Payment.amount).desc())
        )
        result = await db.execute(q)
        rows = result.all()

        total_revenue = sum(int(r.revenue) for r in rows)
        return [
            TopServiceRow(
                service_name=r.service_name,
                booking_count=int(r.booking_count),
                revenue=int(r.revenue),
                percentage=(
                    round(int(r.revenue) / total_revenue * 100, 1)
                    if total_revenue > 0
                    else 0.0
                ),
            )
            for r in rows
        ]

    @staticmethod
    async def get_daily_breakdown(
        db: AsyncSession,
        master_id: uuid.UUID,
        date_from: date,
        date_to: date,
    ) -> list[DailyBreakdownRow]:
        """Return per-day breakdown of bookings, revenue, and utilization."""
        from app.models.booking import Booking
        from app.models.payment import Payment
        from app.models.schedule import MasterSchedule, ScheduleException

        cancelled_statuses = ("cancelled_by_client", "cancelled_by_master")

        # Bookings per day (excluding cancelled)
        bookings_q = (
            select(
                func.date(Booking.starts_at).label("day"),
                func.count(Booking.id).label("cnt"),
            )
            .where(
                and_(
                    Booking.master_id == master_id,
                    func.date(Booking.starts_at) >= date_from,
                    func.date(Booking.starts_at) <= date_to,
                    Booking.status.notin_(cancelled_statuses),
                )
            )
            .group_by(func.date(Booking.starts_at))
        )
        bookings_result = await db.execute(bookings_q)
        bookings_by_day = {
            row.day: int(row.cnt) for row in bookings_result.all()
        }

        # Revenue per day (paid payments by booking start date)
        revenue_q = (
            select(
                func.date(Booking.starts_at).label("day"),
                func.coalesce(func.sum(Payment.amount), 0).label("total"),
            )
            .select_from(Booking)
            .join(Payment, Payment.booking_id == Booking.id)
            .where(
                and_(
                    Booking.master_id == master_id,
                    Payment.status == "paid",
                    func.date(Booking.starts_at) >= date_from,
                    func.date(Booking.starts_at) <= date_to,
                )
            )
            .group_by(func.date(Booking.starts_at))
        )
        revenue_result = await db.execute(revenue_q)
        revenue_by_day = {
            row.day: int(row.total) for row in revenue_result.all()
        }

        # Completed booking minutes per day (for utilization)
        completed_q = select(
            Booking.starts_at, Booking.ends_at
        ).where(
            and_(
                Booking.master_id == master_id,
                func.date(Booking.starts_at) >= date_from,
                func.date(Booking.starts_at) <= date_to,
                Booking.status == "completed",
            )
        )
        completed_result = await db.execute(completed_q)
        completed_minutes_by_day: dict[date, float] = {}
        for row in completed_result.all():
            day = row.starts_at.date()
            mins = (row.ends_at - row.starts_at).total_seconds() / 60
            completed_minutes_by_day[day] = (
                completed_minutes_by_day.get(day, 0) + mins
            )

        # Schedule data for utilization
        schedules_q = select(MasterSchedule).where(
            and_(
                MasterSchedule.master_id == master_id,
                MasterSchedule.is_working == True,  # noqa: E712
            )
        )
        schedules_result = await db.execute(schedules_q)
        schedules = {s.day_of_week: s for s in schedules_result.scalars().all()}

        exceptions_q = select(ScheduleException).where(
            and_(
                ScheduleException.master_id == master_id,
                ScheduleException.exception_date >= date_from,
                ScheduleException.exception_date <= date_to,
            )
        )
        exceptions_result = await db.execute(exceptions_q)
        exceptions = {
            e.exception_date: e for e in exceptions_result.scalars().all()
        }

        # Build rows for each day in range
        rows: list[DailyBreakdownRow] = []
        current = date_from
        while current <= date_to:
            scheduled = _calc_scheduled_minutes(current, current, schedules, exceptions)
            booked = completed_minutes_by_day.get(current, 0)
            util = (
                round(booked / scheduled * 100, 1) if scheduled > 0 else 0.0
            )
            rows.append(
                DailyBreakdownRow(
                    date=current.isoformat(),
                    booking_count=bookings_by_day.get(current, 0),
                    revenue=revenue_by_day.get(current, 0),
                    utilization=util,
                )
            )
            current += timedelta(days=1)

        return rows


def _calc_scheduled_minutes(
    date_from: date,
    date_to: date,
    schedules: dict,
    exceptions: dict,
) -> float:
    """Calculate total scheduled working minutes for a date range.

    Args:
        date_from: Start date (inclusive).
        date_to: End date (inclusive).
        schedules: Dict mapping day_of_week (0=Mon) to MasterSchedule.
        exceptions: Dict mapping date to ScheduleException.

    Returns:
        Total scheduled minutes (breaks subtracted, exceptions applied).
    """
    total = 0.0
    current = date_from
    while current <= date_to:
        exc = exceptions.get(current)
        if exc is not None:
            if exc.is_day_off:
                current += timedelta(days=1)
                continue
            # Custom hours on exception day
            if exc.start_time and exc.end_time:
                start_secs = exc.start_time.hour * 3600 + exc.start_time.minute * 60
                end_secs = exc.end_time.hour * 3600 + exc.end_time.minute * 60
                total += max(0, (end_secs - start_secs)) / 60
            current += timedelta(days=1)
            continue

        dow = current.weekday()  # 0=Monday
        sched = schedules.get(dow)
        if sched is None:
            current += timedelta(days=1)
            continue

        start_secs = sched.start_time.hour * 3600 + sched.start_time.minute * 60
        end_secs = sched.end_time.hour * 3600 + sched.end_time.minute * 60
        day_minutes = max(0, (end_secs - start_secs)) / 60

        # Subtract break
        if sched.break_start and sched.break_end:
            bs = sched.break_start.hour * 3600 + sched.break_start.minute * 60
            be = sched.break_end.hour * 3600 + sched.break_end.minute * 60
            day_minutes -= max(0, (be - bs)) / 60

        total += day_minutes
        current += timedelta(days=1)

    return total
