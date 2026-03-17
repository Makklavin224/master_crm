"""Client service: find-or-create, visit tracking, client listing."""

import uuid
from datetime import datetime

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.booking import Booking
from app.models.client import Client, ClientPlatform, MasterClient
from app.services.phone_service import normalize_phone


async def find_or_create_client(
    db: AsyncSession,
    name: str,
    phone: str,
    platform: str | None = None,
    platform_user_id: str | None = None,
) -> Client:
    """
    Find client by normalized phone or create a new one.
    If platform info is provided, ensure ClientPlatform link exists.
    """
    normalized = normalize_phone(phone)
    if normalized is None:
        # If phone can't be normalized, use raw (validation should catch this upstream)
        normalized = phone

    result = await db.execute(
        select(Client).where(Client.phone == normalized)
    )
    client = result.scalar_one_or_none()

    if client is None:
        client = Client(phone=normalized, name=name)
        db.add(client)
        await db.flush()

    # Ensure platform link exists if provided
    if platform and platform_user_id:
        platform_result = await db.execute(
            select(ClientPlatform).where(
                and_(
                    ClientPlatform.client_id == client.id,
                    ClientPlatform.platform == platform,
                )
            )
        )
        existing_platform = platform_result.scalar_one_or_none()
        if existing_platform is None:
            client_platform = ClientPlatform(
                client_id=client.id,
                platform=platform,
                platform_user_id=platform_user_id,
            )
            db.add(client_platform)
            await db.flush()

    return client


async def get_or_create_master_client(
    db: AsyncSession,
    master_id: uuid.UUID,
    client_id: uuid.UUID,
) -> MasterClient:
    """Find or create a MasterClient link for tracking per-master visit stats."""
    result = await db.execute(
        select(MasterClient).where(
            and_(
                MasterClient.master_id == master_id,
                MasterClient.client_id == client_id,
            )
        )
    )
    mc = result.scalar_one_or_none()

    if mc is None:
        mc = MasterClient(
            master_id=master_id,
            client_id=client_id,
            visit_count=0,
        )
        db.add(mc)
        await db.flush()

    return mc


async def update_visit_stats(
    db: AsyncSession,
    master_client: MasterClient,
    booking_time: datetime,
) -> None:
    """Increment visit_count, update first_visit_at (if null) and last_visit_at."""
    master_client.visit_count += 1
    if master_client.first_visit_at is None:
        master_client.first_visit_at = booking_time
    master_client.last_visit_at = booking_time
    await db.flush()


async def get_master_clients(
    db: AsyncSession,
    master_id: uuid.UUID,
) -> list[MasterClient]:
    """Return all MasterClient records with joined Client data, ordered by last_visit_at desc."""
    result = await db.execute(
        select(MasterClient)
        .where(MasterClient.master_id == master_id)
        .options(selectinload(MasterClient.client))
        .order_by(MasterClient.last_visit_at.desc().nullslast())
    )
    return list(result.scalars().all())


async def get_client_with_history(
    db: AsyncSession,
    master_id: uuid.UUID,
    client_id: uuid.UUID,
) -> tuple[MasterClient | None, list[Booking]]:
    """Return MasterClient + all bookings for that client-master pair."""
    mc_result = await db.execute(
        select(MasterClient)
        .where(
            and_(
                MasterClient.master_id == master_id,
                MasterClient.client_id == client_id,
            )
        )
        .options(selectinload(MasterClient.client))
    )
    mc = mc_result.scalar_one_or_none()

    if mc is None:
        return None, []

    bookings_result = await db.execute(
        select(Booking)
        .where(
            and_(
                Booking.master_id == master_id,
                Booking.client_id == client_id,
            )
        )
        .options(selectinload(Booking.service))
        .order_by(Booking.starts_at.desc())
    )
    bookings = list(bookings_result.scalars().all())

    return mc, bookings
