import asyncio
import io
import logging
import threading
from functools import partial

from PIL import Image

from app.ai.base import ClassificationResult
from app.ai.providers.local_provider import LocalProvider, SCREENSHOT_RESOLUTIONS

logger = logging.getLogger(__name__)

CATEGORY_PROMPTS = {
    "person":    ["a photo of a person", "a photo of people", "a photo of a human face"],
    "landscape": ["a photo of a landscape", "a photo of scenery", "a photo of the outdoors"],
    "food":      ["a photo of food", "a photo of a meal on a plate", "a photo of a dish"],
    "document":  ["a photo of a document", "a photo of printed text on paper"],
    "screenshot":["a screenshot of a phone screen", "a screenshot of a computer screen"],
}

SUBCATEGORY_PROMPTS = {
    "person": {
        "portrait": ["a portrait photo of one person", "a close-up photo of a face"],
        "group":    ["a photo of a group of people", "a photo of multiple people together"],
        "selfie":   ["a selfie photo", "a self-portrait photo taken with a phone"],
    },
    "landscape": {
        "building": ["a photo of a building", "a photo of architecture"],
        "nature":   ["a photo of nature", "a photo of trees or mountains or water"],
        "city":     ["a photo of a city", "a photo of an urban street scene"],
    },
}

CONFIDENCE_THRESHOLD = 0.25

_model = None
_processor = None
_lock = threading.Lock()


def _load_model():
    global _model, _processor
    if _model is None:
        with _lock:
            if _model is None:
                from transformers import CLIPModel, CLIPProcessor
                processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
                model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
                _processor = processor
                _model = model  # assign last — acts as publication gate
    return _model, _processor


def _run_clip(image_bytes: bytes) -> ClassificationResult:
    import torch

    model, processor = _load_model()
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")

    # Build flat prompt list with category index mapping
    all_prompts = []
    category_ranges = {}
    for cat, prompts in CATEGORY_PROMPTS.items():
        start = len(all_prompts)
        all_prompts.extend(prompts)
        category_ranges[cat] = (start, start + len(prompts))

    inputs = processor(text=all_prompts, images=img, return_tensors="pt", padding=True)
    with torch.no_grad():
        outputs = model(**inputs)
        logits = outputs.logits_per_image[0]
        probs = logits.softmax(dim=0).tolist()

    # Average probability per category
    cat_scores = {}
    for cat, (start, end) in category_ranges.items():
        cat_scores[cat] = sum(probs[start:end]) / (end - start)

    best_cat = max(cat_scores, key=cat_scores.get)
    best_score = cat_scores[best_cat]

    if best_score < CONFIDENCE_THRESHOLD:
        return ClassificationResult(category="other", sub_category=None, confidence=round(best_score, 3))

    # Sub-category classification
    sub_category = None
    if best_cat in SUBCATEGORY_PROMPTS:
        sub_prompts_map = SUBCATEGORY_PROMPTS[best_cat]
        sub_all = []
        sub_ranges = {}
        for sub, prompts in sub_prompts_map.items():
            s = len(sub_all)
            sub_all.extend(prompts)
            sub_ranges[sub] = (s, s + len(prompts))

        inputs2 = processor(text=sub_all, images=img, return_tensors="pt", padding=True)
        with torch.no_grad():
            out2 = model(**inputs2)
            sub_probs = out2.logits_per_image[0].softmax(dim=0).tolist()

        sub_scores = {
            sub: sum(sub_probs[s:e]) / (e - s)
            for sub, (s, e) in sub_ranges.items()
        }
        sub_category = max(sub_scores, key=sub_scores.get)

    return ClassificationResult(
        category=best_cat,
        sub_category=sub_category,
        confidence=round(best_score, 3),
    )


class CLIPProvider(LocalProvider):
    """CLIP-based zero-shot image classification. Falls back to LocalProvider on failure."""

    async def classify(self, image_bytes: bytes) -> ClassificationResult:
        try:
            img = Image.open(io.BytesIO(image_bytes))
            w, h = img.size
            if (w, h) in SCREENSHOT_RESOLUTIONS or (h, w) in SCREENSHOT_RESOLUTIONS:
                return ClassificationResult(category="screenshot", sub_category=None, confidence=0.95)
            loop = asyncio.get_running_loop()
            return await loop.run_in_executor(None, partial(_run_clip, image_bytes))
        except Exception as e:
            logger.warning("CLIP classify failed, falling back to rule-based: %s", e)
            return await super().classify(image_bytes)
