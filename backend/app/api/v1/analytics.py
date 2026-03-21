"""Analytics API endpoints: summary, revenue chart, top services, daily breakdown."""

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_master, get_db_with_rls
from app.models.master import Master
from app.schemas.analytics import (
    AnalyticsSummary,
    DailyBreakdownRow,
    RevenueChartPoint,
    TopServiceRow,
)
from app.services.analytics_service import AnalyticsService

router = APIRouter()


@router.get("/summary", response_model=AnalyticsSummary)
async def get_summary(
    master: Annotated[Master, Depends(get_current_master)],
    db: Annotated[AsyncSession, Depends(get_db_with_rls)],
    date_from: date = Query(...),
    date_to: date = Query(...),
):
    """Get summary analytics metrics for a date range."""
    return await AnalyticsService.get_summary(
        db=db,
        master_id=master.id,
        date_from=date_from,
        date_to=date_to,
    )


@router.get("/revenue-chart", response_model=list[RevenueChartPoint])
async def get_revenue_chart(
    master: Annotated[Master, Depends(get_current_master)],
    db: Annotated[AsyncSession, Depends(get_db_with_rls)],
    date_from: date = Query(...),
    date_to: date = Query(...),
):
    """Get daily revenue data points for charting."""
    return await AnalyticsService.get_revenue_chart(
        db=db,
        master_id=master.id,
        date_from=date_from,
        date_to=date_to,
    )


@router.get("/top-services", response_model=list[TopServiceRow])
async def get_top_services(
    master: Annotated[Master, Depends(get_current_master)],
    db: Annotated[AsyncSession, Depends(get_db_with_rls)],
    date_from: date = Query(...),
    date_to: date = Query(...),
):
    """Get services ranked by revenue with booking counts and percentages."""
    return await AnalyticsService.get_top_services(
        db=db,
        master_id=master.id,
        date_from=date_from,
        date_to=date_to,
    )


@router.get("/daily", response_model=list[DailyBreakdownRow])
async def get_daily(
    master: Annotated[Master, Depends(get_current_master)],
    db: Annotated[AsyncSession, Depends(get_db_with_rls)],
    date_from: date = Query(...),
    date_to: date = Query(...),
):
    """Get per-day breakdown of bookings, revenue, and utilization."""
    return await AnalyticsService.get_daily_breakdown(
        db=db,
        master_id=master.id,
        date_from=date_from,
        date_to=date_to,
    )
