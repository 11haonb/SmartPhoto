import io
import pytest

from app.services.photo_service import validate_image, extract_exif
from PIL import Image


def _make_jpeg(width=800, height=600):
    img = Image.new("RGB", (width, height), (128, 128, 128))
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG")
    return buffer.getvalue()


def _make_png(width=800, height=600):
    img = Image.new("RGB", (width, height), (128, 128, 128))
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return buffer.getvalue()


class TestValidateImage:
    def test_valid_jpeg(self):
        data = _make_jpeg()
        mime = validate_image(data, "test.jpg")
        assert mime == "image/jpeg"

    def test_valid_png(self):
        data = _make_png()
        mime = validate_image(data, "test.png")
        assert mime == "image/png"

    def test_reject_too_large(self):
        large_data = b"\xff\xd8\xff\xe0" + b"\x00" * (11 * 1024 * 1024)
        with pytest.raises(ValueError, match="File too large"):
            validate_image(large_data, "big.jpg")

    def test_reject_invalid_type(self):
        with pytest.raises(ValueError, match="Unsupported file type"):
            validate_image(b"not an image", "test.txt")


class TestExtractExif:
    def test_basic_extraction(self):
        data = _make_jpeg()
        result = extract_exif(data)
        assert result["width"] == 800
        assert result["height"] == 600

    def test_no_exif_returns_defaults(self):
        data = _make_jpeg()
        result = extract_exif(data)
        assert result["taken_at"] is None
        assert result["camera_model"] is None
        assert result["gps_latitude"] is None
