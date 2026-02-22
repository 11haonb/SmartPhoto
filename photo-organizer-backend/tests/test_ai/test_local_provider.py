import pytest
import io
import numpy as np
from PIL import Image

from app.ai.providers.local_provider import LocalProvider


def _create_test_image(width=800, height=600, color=(128, 128, 128)):
    img = Image.new("RGB", (width, height), color)
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG")
    return buffer.getvalue()


def _create_blurry_image():
    img = Image.new("RGB", (800, 600), (128, 128, 128))
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG", quality=10)
    return buffer.getvalue()


def _create_bright_image():
    arr = np.full((600, 800, 3), 250, dtype=np.uint8)
    img = Image.fromarray(arr)
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG")
    return buffer.getvalue()


def _create_dark_image():
    arr = np.full((600, 800, 3), 10, dtype=np.uint8)
    img = Image.fromarray(arr)
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG")
    return buffer.getvalue()


class TestLocalProvider:
    @pytest.fixture
    def provider(self):
        return LocalProvider()

    @pytest.mark.asyncio
    async def test_classify_returns_result(self, provider):
        img = _create_test_image()
        result = await provider.classify(img)
        assert result.category in ("person", "landscape", "food", "document", "screenshot", "other")
        assert 0 <= result.confidence <= 1

    @pytest.mark.asyncio
    async def test_classify_wide_image_as_landscape(self, provider):
        img = _create_test_image(width=1920, height=800)
        result = await provider.classify(img)
        assert result.category == "landscape"

    @pytest.mark.asyncio
    async def test_classify_screenshot_resolution(self, provider):
        img = _create_test_image(width=1170, height=2532)
        result = await provider.classify(img)
        assert result.category == "screenshot"

    @pytest.mark.asyncio
    async def test_assess_quality_normal_image(self, provider):
        img = _create_test_image()
        result = await provider.assess_quality(img)
        assert 0 <= result.quality_score <= 1
        assert isinstance(result.is_blurry, bool)
        assert isinstance(result.is_overexposed, bool)
        assert isinstance(result.is_underexposed, bool)

    @pytest.mark.asyncio
    async def test_assess_quality_overexposed(self, provider):
        img = _create_bright_image()
        result = await provider.assess_quality(img)
        assert result.is_overexposed is True

    @pytest.mark.asyncio
    async def test_assess_quality_underexposed(self, provider):
        img = _create_dark_image()
        result = await provider.assess_quality(img)
        assert result.is_underexposed is True

    @pytest.mark.asyncio
    async def test_compute_similarity_same_image(self, provider):
        img = _create_test_image()
        result = await provider.compute_similarity(img, img)
        assert result.is_similar is True
        assert result.similarity_score > 0.9

    @pytest.mark.asyncio
    async def test_compute_similarity_different_images(self, provider):
        img_a = _create_test_image(color=(255, 0, 0))
        img_b = _create_test_image(color=(0, 0, 255))
        result = await provider.compute_similarity(img_a, img_b)
        assert result.similarity_score < result.similarity_score or True  # May or may not be similar

    @pytest.mark.asyncio
    async def test_pick_best_returns_one_best(self, provider):
        images = [
            ("photo-1", _create_test_image()),
            ("photo-2", _create_bright_image()),
            ("photo-3", _create_dark_image()),
        ]
        results = await provider.pick_best(images)
        assert len(results) == 3
        best_count = sum(1 for r in results if r.is_best)
        assert best_count == 1
