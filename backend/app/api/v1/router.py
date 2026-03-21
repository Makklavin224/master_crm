from fastapi import APIRouter

from app.api.v1.analytics import router as analytics_router
from app.api.v1.auth import router as auth_router
from app.api.v1.bookings import router as bookings_router
from app.api.v1.client_auth import router as client_auth_router
from app.api.v1.client_cabinet import router as client_cabinet_router
from app.api.v1.clients import router as clients_router
from app.api.v1.health import router as health_router
from app.api.v1.masters import router as masters_router
from app.api.v1.payments import router as payments_router
from app.api.v1.portfolio import media_router
from app.api.v1.portfolio import router as portfolio_router
from app.api.v1.public import router as public_router
from app.api.v1.reviews import router as reviews_router
from app.api.v1.schedule import router as schedule_router
from app.api.v1.services import router as services_router
from app.api.v1.settings import router as settings_router

api_v1_router = APIRouter()
api_v1_router.include_router(health_router, tags=["health"])
api_v1_router.include_router(auth_router)
api_v1_router.include_router(
    services_router, prefix="/services", tags=["services"]
)
api_v1_router.include_router(
    schedule_router, prefix="/schedule", tags=["schedule"]
)
api_v1_router.include_router(
    bookings_router, prefix="/bookings", tags=["bookings"]
)
api_v1_router.include_router(
    clients_router, prefix="/clients", tags=["clients"]
)
api_v1_router.include_router(
    settings_router, prefix="/settings", tags=["settings"]
)
api_v1_router.include_router(
    masters_router, prefix="/masters", tags=["masters"]
)
api_v1_router.include_router(
    public_router, prefix="/masters", tags=["public"]
)
api_v1_router.include_router(
    analytics_router, prefix="/analytics", tags=["analytics"]
)
api_v1_router.include_router(
    payments_router, prefix="/payments", tags=["payments"]
)
api_v1_router.include_router(
    reviews_router, prefix="/reviews", tags=["reviews"]
)
api_v1_router.include_router(
    portfolio_router, prefix="/portfolio", tags=["portfolio"]
)
api_v1_router.include_router(media_router, tags=["media"])
api_v1_router.include_router(
    client_auth_router, prefix="/client/auth", tags=["client-auth"]
)
api_v1_router.include_router(
    client_cabinet_router, prefix="/client", tags=["client-cabinet"]
)
