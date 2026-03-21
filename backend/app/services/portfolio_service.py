"""Portfolio photo processing: resize, thumbnail generation, file management."""

import asyncio
import io
import uuid
from pathlib import Path

from PIL import Image

ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}
EXTENSION_MAP = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}


class PortfolioService:
    @staticmethod
    async def process_upload(
        master_id: uuid.UUID,
        file_content: bytes,
        content_type: str,
        settings,  # app.core.config.Settings
    ) -> tuple[str, str]:
        """Process upload: validate, resize, create thumbnail, save to disk.

        Returns (file_path, thumbnail_path) relative paths for DB storage.
        Raises ValueError on validation failure.
        """
        # Validate content type
        if content_type not in ALLOWED_CONTENT_TYPES:
            raise ValueError(
                "Формат файла не поддерживается. Допустимые: JPEG, PNG, WebP"
            )

        # Validate file size
        if len(file_content) > settings.portfolio_max_file_size:
            raise ValueError("Файл слишком большой. Максимум 5 МБ")

        def _process() -> tuple[str, str]:
            # Verify image integrity
            verify_img = Image.open(io.BytesIO(file_content))
            verify_img.verify()

            # Re-open for actual processing (verify() invalidates the image)
            img = Image.open(io.BytesIO(file_content))

            # Convert RGBA to RGB for JPEG compatibility
            if img.mode == "RGBA":
                img = img.convert("RGB")

            # Generate unique filename
            ext = EXTENSION_MAP[content_type]
            filename = f"{uuid.uuid4()}{ext}"

            # Create master directory
            master_dir = Path(settings.portfolio_base_path) / str(master_id)
            master_dir.mkdir(parents=True, exist_ok=True)

            # Full-size: downsize to max dimension, preserve aspect ratio
            img.thumbnail(
                (settings.portfolio_full_size, settings.portfolio_full_size),
                Image.LANCZOS,
            )

            # Save full-size
            full_path = master_dir / filename
            save_kwargs = {"optimize": True}
            if content_type == "image/jpeg":
                save_kwargs["quality"] = 85
            img.save(str(full_path), **save_kwargs)

            # Thumbnail: create copy, downsize further
            thumb = img.copy()
            thumb.thumbnail(
                (settings.portfolio_thumb_size, settings.portfolio_thumb_size),
                Image.LANCZOS,
            )
            thumb_filename = f"thumb_{filename}"
            thumb_path = master_dir / thumb_filename
            thumb.save(str(thumb_path), **save_kwargs)

            # Return relative paths for DB storage
            rel_file = f"{master_id}/{filename}"
            rel_thumb = f"{master_id}/{thumb_filename}"
            return rel_file, rel_thumb

        return await asyncio.to_thread(_process)

    @staticmethod
    async def delete_files(
        file_path: str, thumbnail_path: str, settings
    ) -> None:
        """Delete photo files from disk. Silently ignores missing files."""

        def _delete() -> None:
            base = Path(settings.portfolio_base_path)
            (base / file_path).unlink(missing_ok=True)
            (base / thumbnail_path).unlink(missing_ok=True)

        await asyncio.to_thread(_delete)
