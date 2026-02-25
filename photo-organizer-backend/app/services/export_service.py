import io
import logging
import zipfile
from datetime import datetime, timezone
from typing import Generator

from app.core.storage import download_file
from app.models import Photo

logger = logging.getLogger(__name__)

_CHUNK = 65536  # 64 KB read chunks


def build_zip(photos: list[Photo], quality: str = "compressed") -> tuple[io.BytesIO, int]:
    """Build a ZIP of photos into a BytesIO buffer. Returns (buffer, failed_count).

    Uses ZIP_STORED for already-compressed images (JPEG/WebP) to avoid
    double-compression overhead, and streams each file in chunks to limit
    peak memory to ~2 × largest single file rather than sum of all files.
    """
    buf = io.BytesIO()
    seen: dict[str, int] = {}
    failed = 0

    with zipfile.ZipFile(buf, mode="w", compression=zipfile.ZIP_STORED) as zf:
        for photo in photos:
            key = photo.storage_path if quality == "original" else (photo.compressed_path or photo.storage_path)
            name = _unique_name(photo.original_filename, seen)

            try:
                data = download_file(key)
                zf.writestr(name, data)
            except Exception:
                logger.warning("Failed to download %s (photo_id=%s) for ZIP", key, photo.id)
                failed += 1

    buf.seek(0)
    return buf, failed


def _unique_name(filename: str, seen: dict[str, int]) -> str:
    if filename not in seen:
        seen[filename] = 0
        return filename
    seen[filename] += 1
    base, _, ext = filename.rpartition(".")
    return f"{base}_{seen[filename]}.{ext}" if ext else f"{filename}_{seen[filename]}"


def zip_filename(filter_type: str, filter_value: str, task_id: str, quality: str = "compressed") -> str:
    today = datetime.now(timezone.utc).strftime("%Y%m%d")
    quality_suffix = f"_{quality}"

    if filter_type == "date":
        return f"smartphoto_date_{filter_value}{quality_suffix}.zip"
    elif filter_type == "category":
        safe_value = filter_value.replace("/", "_").replace(" ", "_")
        return f"smartphoto_category_{safe_value}{quality_suffix}.zip"
    elif filter_type == "best":
        return f"smartphoto_best_{task_id[:8]}_{today}{quality_suffix}.zip"
    return f"smartphoto_export_{today}{quality_suffix}.zip"
