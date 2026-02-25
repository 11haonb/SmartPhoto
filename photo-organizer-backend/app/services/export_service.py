import io
import logging
import zipfile
from datetime import datetime, timezone

from app.core.storage import download_file
from app.models import Photo

logger = logging.getLogger(__name__)


def build_zip(photos: list[Photo], quality: str = "compressed") -> tuple[io.BytesIO, int]:
    """Build a ZIP of photos. Returns (buffer, failed_count)."""
    buf = io.BytesIO()
    seen: dict[str, int] = {}
    failed = 0

    with zipfile.ZipFile(buf, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        for photo in photos:
            key = photo.storage_path if quality == "original" else (photo.compressed_path or photo.storage_path)
            name = photo.original_filename

            if name in seen:
                seen[name] += 1
                base, _, ext = name.rpartition(".")
                name = f"{base}_{seen[name]}.{ext}" if ext else f"{name}_{seen[name]}"
            else:
                seen[name] = 0

            try:
                data = download_file(key)
                zf.writestr(name, data)
            except Exception:
                logger.warning("Failed to download %s (photo_id=%s) for ZIP", key, photo.id)
                failed += 1

    buf.seek(0)
    return buf, failed


def zip_filename(filter_type: str, filter_value: str, task_id: str, quality: str = "compressed") -> str:
    today = datetime.now(timezone.utc).strftime("%Y%m%d")
    quality_suffix = f"_{quality}"

    if filter_type == "date":
        return f"smartphoto_date_{filter_value}{quality_suffix}.zip"
    elif filter_type == "category":
        return f"smartphoto_category_{filter_value}{quality_suffix}.zip"
    elif filter_type == "best":
        return f"smartphoto_best_{task_id[:8]}_{today}{quality_suffix}.zip"
    return f"smartphoto_export_{today}{quality_suffix}.zip"
