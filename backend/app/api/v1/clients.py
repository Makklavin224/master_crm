"""Client list and history endpoints."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_master, get_db_with_rls
from app.models.master import Master
from app.schemas.booking import BookingRead
from app.schemas.client import ClientDetailRead, ClientRead, MasterClientRead
from app.services.client_service import get_client_with_history, get_master_clients

router = APIRouter()


@router.get("", response_model=list[MasterClientRead])
async def list_clients(
    master: Annotated[Master, Depends(get_current_master)],
    db: Annotated[AsyncSession, Depends(get_db_with_rls)],
):
    """List master's clients with visit stats (RLS-scoped)."""
    master_clients = await get_master_clients(db, master.id)
    return master_clients


@router.get("/{client_id}", response_model=ClientDetailRead)
async def get_client_detail(
    client_id: uuid.UUID,
    master: Annotated[Master, Depends(get_current_master)],
    db: Annotated[AsyncSession, Depends(get_db_with_rls)],
):
    """Get client detail with booking history."""
    mc, bookings = await get_client_with_history(db, master.id, client_id)
    if mc is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found",
        )

    booking_reads = []
    for b in bookings:
        booking_reads.append(
            BookingRead(
                id=b.id,
                master_id=b.master_id,
                client_id=b.client_id,
                service_id=b.service_id,
                starts_at=b.starts_at,
                ends_at=b.ends_at,
                status=b.status,
                source_platform=b.source_platform,
                notes=b.notes,
                created_at=b.created_at,
                service_name=b.service.name if b.service else None,
                client_name=mc.client.name if mc.client else None,
                client_phone=mc.client.phone if mc.client else None,
            )
        )

    return ClientDetailRead(
        client=ClientRead.model_validate(mc.client),
        bookings=booking_reads,
        visit_count=mc.visit_count,
    )
