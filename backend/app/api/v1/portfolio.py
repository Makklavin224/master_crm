"""Portfolio CRUD endpoints (master-facing, JWT auth) + public media serving."""

import asyncio
import uuid
from pathlib import Path
from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    Form,
    HTTPException,
    UploadFile,
    status,
)
from fastapi.responses import FileResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.dependencies import get_current_master, get_db_with_rls
from app.models.master import Master
from app.models.portfolio_photo import PortfolioPhoto
from app.schemas.portfolio import (
    PortfolioPhotoRead,
    PortfolioPhotoUpdate,
    PortfolioReorderRequest,
)
from app.services.portfolio_service import PortfolioService

router = APIRouter()


# --- Master-facing CRUD (JWT auth + RLS) ---


@router.post("/upload", response_model=PortfolioPhotoRead, status_code=201)
async def upload_photo(
    file: UploadFile,
    master: Annotated[Master, Depends(get_current_master)],
    db: Annotated[AsyncSession, Depends(get_db_with_rls)],
    service_tag: str | None = Form(default=None),
    caption: str | None = Form(default=None),
):
    """Upload a portfolio photo. Auto-resizes to 1200px and generates 300px thumbnail."""
    # Check photo count limit
    count_result = await db.execute(
        select(func.count(PortfolioPhoto.id)).where(
            PortfolioPhoto.master_id == master.id
        )
    )
    current_count = count_result.scalar_one()
    if current_count >= settings.portfolio_max_photos:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Максимум {settings.portfolio_max_photos} фото",
        )

    # Read file content
    content = await file.read()

    # Process upload (validate + resize + thumbnail)
    try:
        file_path, thumbnail_path = await PortfolioService.process_upload(
            master.id, content, file.content_type, settings
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    # Get next sort_order
    max_order_result = await db.execute(
        select(func.coalesce(func.max(PortfolioPhoto.sort_order), -1)).where(
            PortfolioPhoto.master_id == master.id
        )
    )
    next_order = max_order_result.scalar_one() + 1

    # Create DB record
    photo = PortfolioPhoto(
        master_id=master.id,
        file_path=file_path,
        thumbnail_path=thumbnail_path,
        caption=caption,
        service_tag=service_tag,
        sort_order=next_order,
    )
    db.add(photo)
    await db.flush()
    await db.refresh(photo)

    return photo


@router.get("/", response_model=list[PortfolioPhotoRead])
async def list_photos(
    master: Annotated[Master, Depends(get_current_master)],
    db: Annotated[AsyncSession, Depends(get_db_with_rls)],
):
    """List all portfolio photos for the current master, ordered by sort_order."""
    result = await db.execute(
        select(PortfolioPhoto).order_by(PortfolioPhoto.sort_order)
    )
    return result.scalars().all()


@router.put("/reorder", status_code=204)
async def reorder_photos(
    data: PortfolioReorderRequest,
    master: Annotated[Master, Depends(get_current_master)],
    db: Annotated[AsyncSession, Depends(get_db_with_rls)],
):
    """Bulk-reorder portfolio photos by setting sort_order for each."""
    for item in data.items:
        result = await db.execute(
            select(PortfolioPhoto).where(PortfolioPhoto.id == item.id)
        )
        photo = result.scalar_one_or_none()
        if photo is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Photo {item.id} not found",
            )
        photo.sort_order = item.sort_order
    await db.flush()


@router.put("/{photo_id}", response_model=PortfolioPhotoRead)
async def update_photo(
    photo_id: uuid.UUID,
    data: PortfolioPhotoUpdate,
    master: Annotated[Master, Depends(get_current_master)],
    db: Annotated[AsyncSession, Depends(get_db_with_rls)],
):
    """Update caption and/or service_tag of a portfolio photo."""
    result = await db.execute(
        select(PortfolioPhoto).where(PortfolioPhoto.id == photo_id)
    )
    photo = result.scalar_one_or_none()
    if photo is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Photo not found",
        )

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(photo, field, value)

    await db.flush()
    await db.refresh(photo)
    return photo


@router.delete("/{photo_id}", status_code=204)
async def delete_photo(
    photo_id: uuid.UUID,
    master: Annotated[Master, Depends(get_current_master)],
    db: Annotated[AsyncSession, Depends(get_db_with_rls)],
):
    """Delete a portfolio photo (DB record + files from disk)."""
    result = await db.execute(
        select(PortfolioPhoto).where(PortfolioPhoto.id == photo_id)
    )
    photo = result.scalar_one_or_none()
    if photo is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Photo not found",
        )

    # Delete files from disk
    await PortfolioService.delete_files(
        photo.file_path, photo.thumbnail_path, settings
    )

    # Delete DB record
    await db.delete(photo)
    await db.flush()


# --- Public media serving (no auth) ---

media_router = APIRouter()


@media_router.get("/media/{file_path:path}")
async def serve_media(file_path: str):
    """Serve portfolio media files. No authentication required."""
    # Sanitize path: reject directory traversal
    if ".." in file_path:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid path",
        )

    full_path = Path(settings.portfolio_base_path) / file_path

    # Check file exists (in thread to avoid blocking)
    exists = await asyncio.to_thread(full_path.is_file)
    if not exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found",
        )

    return FileResponse(str(full_path))
