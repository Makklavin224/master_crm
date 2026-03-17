from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.bookings import router as bookings_router
from app.api.v1.clients import router as clients_router
from app.api.v1.health import router as health_router
from app.api.v1.masters import router as masters_router
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
