"""Service CRUD endpoints."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_master, get_db, get_db_with_rls
from app.models.master import Master
from app.models.service import Service
from app.schemas.service import ServiceCreate, ServiceRead, ServiceUpdate

router = APIRouter()


@router.post("", response_model=ServiceRead, status_code=201)
async def create_service(
    data: ServiceCreate,
    master: Annotated[Master, Depends(get_current_master)],
    db: Annotated[AsyncSession, Depends(get_db_with_rls)],
):
    """Create a new service for the authenticated master."""
    service = Service(
        master_id=master.id,
        name=data.name,
        duration_minutes=data.duration_minutes,
        price=data.price,
        category=data.category,
        description=data.description,
    )
    db.add(service)
    await db.flush()
    await db.refresh(service)
    return service


@router.get("", response_model=list[ServiceRead])
async def list_services(
    master: Annotated[Master, Depends(get_current_master)],
    db: Annotated[AsyncSession, Depends(get_db_with_rls)],
):
    """List active services for the authenticated master (RLS-scoped)."""
    result = await db.execute(
        select(Service).where(Service.is_active.is_(True)).order_by(Service.sort_order)
    )
    return result.scalars().all()


@router.put("/{service_id}", response_model=ServiceRead)
async def update_service(
    service_id: uuid.UUID,
    data: ServiceUpdate,
    master: Annotated[Master, Depends(get_current_master)],
    db: Annotated[AsyncSession, Depends(get_db_with_rls)],
):
    """Update a service (RLS ensures it belongs to the current master)."""
    result = await db.execute(select(Service).where(Service.id == service_id))
    service = result.scalar_one_or_none()
    if service is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Service not found"
        )

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(service, field, value)

    await db.flush()
    await db.refresh(service)
    return service


@router.delete("/{service_id}", status_code=204)
async def delete_service(
    service_id: uuid.UUID,
    master: Annotated[Master, Depends(get_current_master)],
    db: Annotated[AsyncSession, Depends(get_db_with_rls)],
):
    """Soft-delete a service (set is_active=False)."""
    result = await db.execute(select(Service).where(Service.id == service_id))
    service = result.scalar_one_or_none()
    if service is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Service not found"
        )

    service.is_active = False
    await db.flush()
