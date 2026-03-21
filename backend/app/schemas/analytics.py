"""Analytics schemas for API response validation."""

from pydantic import BaseModel


class AnalyticsSummary(BaseModel):
    """Summary metrics for the analytics dashboard."""

    revenue: int  # in kopecks
    booking_count: int
    client_count: int
    new_clients: int
    repeat_clients: int
    utilization: float  # 0-100%
    avg_check: int  # in kopecks
    retention_rate: float  # 0-100%
    cancel_rate: float  # 0-100%
    noshow_rate: float  # 0-100%


class RevenueChartPoint(BaseModel):
    """Single data point for revenue over time chart."""

    date: str  # "YYYY-MM-DD"
    revenue: int  # in kopecks


class TopServiceRow(BaseModel):
    """Service ranked by revenue."""

    service_name: str
    booking_count: int
    revenue: int  # in kopecks
    percentage: float  # 0-100


class DailyBreakdownRow(BaseModel):
    """Per-day breakdown of bookings, revenue, and utilization."""

    date: str  # "YYYY-MM-DD"
    booking_count: int
    revenue: int  # in kopecks
    utilization: float  # 0-100%
