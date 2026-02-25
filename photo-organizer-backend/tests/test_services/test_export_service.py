import io
import zipfile
from unittest.mock import MagicMock, patch

import pytest

from app.services.export_service import build_zip, zip_filename


def _make_photo(filename, storage_path, compressed_path=None):
    photo = MagicMock()
    photo.id = "test-id"
    photo.original_filename = filename
    photo.storage_path = storage_path
    photo.compressed_path = compressed_path
    return photo


class TestBuildZip:
    def test_empty_photos_returns_valid_zip(self):
        buf, failed = build_zip([])
        assert failed == 0
        with zipfile.ZipFile(buf) as zf:
            assert zf.namelist() == []

    def test_single_photo_compressed(self):
        photo = _make_photo("test.jpg", "originals/1.jpg", "compressed/1.jpg")
        with patch("app.services.export_service.download_file", return_value=b"imgdata"):
            buf, failed = build_zip([photo], quality="compressed")
        assert failed == 0
        with zipfile.ZipFile(buf) as zf:
            assert "test.jpg" in zf.namelist()
            assert zf.read("test.jpg") == b"imgdata"

    def test_single_photo_original(self):
        photo = _make_photo("test.jpg", "originals/1.jpg", "compressed/1.jpg")
        with patch("app.services.export_service.download_file", return_value=b"origdata") as mock_dl:
            buf, failed = build_zip([photo], quality="original")
        mock_dl.assert_called_once_with("originals/1.jpg")
        assert failed == 0

    def test_falls_back_to_storage_path_when_no_compressed(self):
        photo = _make_photo("test.jpg", "originals/1.jpg", compressed_path=None)
        with patch("app.services.export_service.download_file", return_value=b"data") as mock_dl:
            buf, failed = build_zip([photo], quality="compressed")
        mock_dl.assert_called_once_with("originals/1.jpg")
        assert failed == 0

    def test_duplicate_filenames_are_deduped(self):
        photos = [
            _make_photo("photo.jpg", "originals/1.jpg", "compressed/1.jpg"),
            _make_photo("photo.jpg", "originals/2.jpg", "compressed/2.jpg"),
        ]
        with patch("app.services.export_service.download_file", return_value=b"data"):
            buf, failed = build_zip(photos)
        with zipfile.ZipFile(buf) as zf:
            names = zf.namelist()
            assert len(names) == 2
            assert len(set(names)) == 2

    def test_failed_download_counted(self):
        photo = _make_photo("bad.jpg", "originals/bad.jpg")
        with patch("app.services.export_service.download_file", side_effect=Exception("S3 error")):
            buf, failed = build_zip([photo])
        assert failed == 1

    def test_partial_failure_still_returns_zip(self):
        photos = [
            _make_photo("good.jpg", "originals/good.jpg", "compressed/good.jpg"),
            _make_photo("bad.jpg", "originals/bad.jpg"),
        ]

        def side_effect(key):
            if "bad" in key:
                raise Exception("not found")
            return b"gooddata"

        with patch("app.services.export_service.download_file", side_effect=side_effect):
            buf, failed = build_zip(photos)
        assert failed == 1
        with zipfile.ZipFile(buf) as zf:
            assert "good.jpg" in zf.namelist()


class TestZipFilename:
    def test_date_filter(self):
        name = zip_filename("date", "2026-02-25", "abc12345", "compressed")
        assert name == "smartphoto_date_2026-02-25_compressed.zip"

    def test_category_filter(self):
        name = zip_filename("category", "landscape", "abc12345", "original")
        assert name == "smartphoto_category_landscape_original.zip"

    def test_best_filter(self):
        name = zip_filename("best", "", "abc12345-xxxx", "compressed")
        assert name.startswith("smartphoto_best_abc12345")
        assert "_compressed.zip" in name

    def test_unknown_filter_returns_fallback(self):
        name = zip_filename("unknown", "", "abc12345", "compressed")
        assert name.startswith("smartphoto_export_")
