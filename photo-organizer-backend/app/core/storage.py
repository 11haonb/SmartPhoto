import io
import logging
from uuid import UUID

import boto3
from botocore.config import Config as BotoConfig
from PIL import Image

from app.core.config import settings

logger = logging.getLogger(__name__)


def _get_s3_client():
    return boto3.client(
        "s3",
        endpoint_url=settings.STORAGE_ENDPOINT,
        aws_access_key_id=settings.STORAGE_ACCESS_KEY,
        aws_secret_access_key=settings.STORAGE_SECRET_KEY,
        region_name=settings.STORAGE_REGION,
        config=BotoConfig(signature_version="s3v4"),
    )


def upload_file(file_bytes: bytes, key: str, content_type: str) -> str:
    client = _get_s3_client()
    client.put_object(
        Bucket=settings.STORAGE_BUCKET,
        Key=key,
        Body=file_bytes,
        ContentType=content_type,
    )
    return f"{settings.STORAGE_ENDPOINT}/{settings.STORAGE_BUCKET}/{key}"


def delete_file(key: str) -> None:
    client = _get_s3_client()
    client.delete_object(Bucket=settings.STORAGE_BUCKET, Key=key)


def get_file_url(key: str) -> str:
    base = settings.STORAGE_PUBLIC_URL or settings.STORAGE_ENDPOINT
    return f"{base}/{settings.STORAGE_BUCKET}/{key}"


def generate_thumbnail(image_bytes: bytes, size: int = 300) -> bytes:
    img = Image.open(io.BytesIO(image_bytes))
    img.thumbnail((size, size), Image.Resampling.LANCZOS)

    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")

    buffer = io.BytesIO()
    img.save(buffer, format="JPEG", quality=85)
    return buffer.getvalue()


def generate_compressed(image_bytes: bytes, max_side: int = 1200) -> bytes:
    img = Image.open(io.BytesIO(image_bytes))

    ratio = min(max_side / img.width, max_side / img.height)
    if ratio < 1:
        new_size = (int(img.width * ratio), int(img.height * ratio))
        img = img.resize(new_size, Image.Resampling.LANCZOS)

    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")

    buffer = io.BytesIO()
    img.save(buffer, format="JPEG", quality=80)
    return buffer.getvalue()


def upload_photo_with_variants(
    photo_id: UUID,
    file_bytes: bytes,
    content_type: str,
) -> dict[str, str]:
    original_key = f"originals/{photo_id}.jpg"
    thumbnail_key = f"thumbnails/{photo_id}.jpg"
    compressed_key = f"compressed/{photo_id}.jpg"

    upload_file(file_bytes, original_key, content_type)

    try:
        thumb_bytes = generate_thumbnail(file_bytes, settings.THUMBNAIL_SIZE)
        upload_file(thumb_bytes, thumbnail_key, "image/jpeg")
    except Exception:
        logger.warning("Failed to generate thumbnail for %s", photo_id)
        thumbnail_key = None

    try:
        comp_bytes = generate_compressed(file_bytes, settings.COMPRESSED_SIZE)
        upload_file(comp_bytes, compressed_key, "image/jpeg")
    except Exception:
        logger.warning("Failed to generate compressed for %s", photo_id)
        compressed_key = None

    return {
        "storage_path": original_key,
        "thumbnail_path": thumbnail_key,
        "compressed_path": compressed_key,
    }
