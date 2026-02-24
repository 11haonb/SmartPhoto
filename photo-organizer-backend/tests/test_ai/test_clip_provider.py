import io
import pytest
from unittest.mock import patch
from PIL import Image

from app.ai.providers.clip_provider import CLIPProvider, CATEGORY_PROMPTS, SUBCATEGORY_PROMPTS
from app.ai.base import ClassificationResult


def _make_image(width=800, height=600, color=(128, 128, 128)) -> bytes:
    img = Image.new("RGB", (width, height), color)
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


@pytest.fixture
def provider():
    return CLIPProvider()


@pytest.mark.asyncio
async def test_classify_returns_valid_result(provider):
    with patch("app.ai.providers.clip_provider._run_clip") as mock_clip:
        mock_clip.return_value = ClassificationResult(category="landscape", sub_category="nature", confidence=0.7)
        result = await provider.classify(_make_image())
    assert result.category in ("person", "landscape", "food", "document", "screenshot", "other")
    assert 0.0 <= result.confidence <= 1.0


@pytest.mark.asyncio
async def test_screenshot_fast_path(provider):
    img = _make_image(width=1170, height=2532)
    result = await provider.classify(img)
    assert result.category == "screenshot"
    assert result.confidence >= 0.9


@pytest.mark.asyncio
async def test_screenshot_rotated(provider):
    img = _make_image(width=2532, height=1170)
    result = await provider.classify(img)
    assert result.category == "screenshot"


@pytest.mark.asyncio
async def test_fallback_on_model_failure(provider):
    with patch("app.ai.providers.clip_provider._run_clip", side_effect=RuntimeError("model load failed")):
        # Wide image → LocalProvider returns landscape
        result = await provider.classify(_make_image(width=1920, height=800))
    assert result.category in ("person", "landscape", "food", "document", "screenshot", "other")


@pytest.mark.asyncio
async def test_assess_quality_inherited(provider):
    result = await provider.assess_quality(_make_image())
    assert 0.0 <= result.quality_score <= 1.0
    assert isinstance(result.is_blurry, bool)


@pytest.mark.asyncio
async def test_compute_similarity_inherited(provider):
    img = _make_image()
    result = await provider.compute_similarity(img, img)
    assert result.is_similar is True
    assert result.similarity_score > 0.9


@pytest.mark.asyncio
async def test_pick_best_inherited(provider):
    images = [("a", _make_image()), ("b", _make_image(color=(200, 200, 200)))]
    results = await provider.pick_best(images)
    assert len(results) == 2
    assert sum(1 for r in results if r.is_best) == 1


def test_all_categories_have_prompts():
    for cat in ("person", "landscape", "food", "document", "screenshot"):
        assert cat in CATEGORY_PROMPTS
        assert len(CATEGORY_PROMPTS[cat]) >= 2


def test_subcategory_prompts_coverage():
    for cat in ("person", "landscape"):
        assert cat in SUBCATEGORY_PROMPTS
        for sub, prompts in SUBCATEGORY_PROMPTS[cat].items():
            assert len(prompts) >= 1, f"{cat}.{sub} has no prompts"
