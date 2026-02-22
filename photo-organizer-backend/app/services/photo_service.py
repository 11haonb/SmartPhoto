import io
import logging
from datetime import datetime, timezone
from uuid import UUID

import magic
from PIL import Image
from PIL.ExifTags import Base as ExifBase

from app.core.config import settings
from app.core.storage import upload_photo_with_variants, delete_file, get_file_url

logger = logging.getLogger(__name__)

ALLOWED_MIME_TYPES = {
    "image/jpeg",
    "image/png",
    "image/heic",
    "image/heif",
    "image/webp",
}


def validate_image(file_bytes: bytes, filename: str) -> str:
    if len(file_bytes) > settings.MAX_UPLOAD_SIZE:
        raise ValueError(f"File too large: max {settings.MAX_UPLOAD_SIZE // (1024 * 1024)}MB")

    mime_type = magic.from_buffer(file_bytes, mime=True)
    if mime_type not in ALLOWED_MIME_TYPES:
        raise ValueError(f"Unsupported file type: {mime_type}. Allowed: JPEG, PNG, HEIC, WebP")

    try:
        img = Image.open(io.BytesIO(file_bytes))
        total_pixels = img.width * img.height
        if total_pixels > settings.MAX_IMAGE_PIXELS:
            raise ValueError(f"Image too large: {total_pixels} pixels (max {settings.MAX_IMAGE_PIXELS})")
    except (Image.UnidentifiedImageError, Image.DecompressionBombError) as e:
        raise ValueError(f"Invalid image file: {e}")

    return mime_type


def extract_exif(file_bytes: bytes) -> dict:
    result = {
        "taken_at": None,
        "camera_model": None,
        "gps_latitude": None,
        "gps_longitude": None,
        "orientation": None,
        "width": None,
        "height": None,
    }

    try:
        img = Image.open(io.BytesIO(file_bytes))
        result["width"] = img.width
        result["height"] = img.height

        exif_data = img.getexif()
        if not exif_data:
            return result

        # DateTimeOriginal (tag 36867)
        date_str = exif_data.get(36867) or exif_data.get(306)
        if date_str:
            try:
                result["taken_at"] = datetime.strptime(
                    date_str, "%Y:%m:%d %H:%M:%S"
                ).replace(tzinfo=timezone.utc)
            except (ValueError, TypeError):
                pass

        # Camera model (tag 272)
        result["camera_model"] = exif_data.get(272)

        # Orientation (tag 274)
        result["orientation"] = exif_data.get(274)

        # GPS info (tag 34853)
        gps_info = exif_data.get_ifd(34853)
        if gps_info:
            lat = _convert_gps_coordinate(gps_info.get(2), gps_info.get(1))
            lon = _convert_gps_coordinate(gps_info.get(4), gps_info.get(3))
            result["gps_latitude"] = lat
            result["gps_longitude"] = lon

    except Exception:
        logger.warning("Failed to extract EXIF data", exc_info=True)

    return result


def _convert_gps_coordinate(coord, ref) -> float | None:
    if coord is None or ref is None:
        return None
    try:
        degrees = float(coord[0])
        minutes = float(coord[1])
        seconds = float(coord[2])
        value = degrees + minutes / 60 + seconds / 3600
        if ref in ("S", "W"):
            value = -value
        return value
    except (TypeError, IndexError, ValueError):
        return None


async def process_upload(
    photo_id: UUID,
    file_bytes: bytes,
    filename: str,
) -> dict:
    mime_type = validate_image(file_bytes, filename)
    exif_data = extract_exif(file_bytes)

    paths = upload_photo_with_variants(photo_id, file_bytes, mime_type)

    return {
        "mime_type": mime_type,
        "file_size": len(file_bytes),
        **exif_data,
        **paths,
    }


def get_photo_urls(photo) -> dict:
    return {
        "thumbnail_url": get_file_url(photo.thumbnail_path) if photo.thumbnail_path else None,
        "compressed_url": get_file_url(photo.compressed_path) if photo.compressed_path else None,
    }
