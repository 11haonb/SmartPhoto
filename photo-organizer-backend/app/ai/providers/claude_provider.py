import base64
import json
import logging

import httpx

from app.ai.base import (
    AIProvider,
    BestPickResult,
    ClassificationResult,
    QualityResult,
    SimilarityResult,
)

logger = logging.getLogger(__name__)

CLASSIFY_PROMPT = """Analyze this image and classify it into one of these categories:
- person (sub: portrait, group, selfie)
- landscape (sub: building, nature, city)
- food
- document
- screenshot
- other

Respond with JSON only: {"category": "...", "sub_category": "..." or null, "confidence": 0.0-1.0}"""

QUALITY_PROMPT = """Assess the quality of this photo. Check for:
- Blurriness
- Overexposure (too bright)
- Underexposure (too dark)
- Whether it's a screenshot

Respond with JSON only:
{"quality_score": 0.0-1.0, "is_blurry": bool, "is_overexposed": bool, "is_underexposed": bool, "is_screenshot": bool, "is_invalid": bool, "invalid_reason": "..." or null}"""

SIMILARITY_PROMPT = """Compare these two images. Are they similar photos (e.g., same scene, burst shots)?
Respond with JSON only: {"is_similar": bool, "similarity_score": 0.0-1.0}"""

BEST_PICK_PROMPT = """These are similar photos from the same group. Pick the best one based on:
- Sharpness/clarity
- Exposure quality
- Composition
- Facial expressions (if people)

For each photo, provide a score. Respond with JSON array:
[{"photo_index": 0, "score": 0.0-1.0, "is_best": bool, "reason": "..."}]"""


class ClaudeProvider(AIProvider):
    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514"):
        self._api_key = api_key
        self._model = model
        self._base_url = "https://api.anthropic.com/v1"

    async def _call_vision(self, image_bytes: bytes, prompt: str) -> str:
        b64 = base64.b64encode(image_bytes).decode("utf-8")
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                f"{self._base_url}/messages",
                headers={
                    "x-api-key": self._api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": self._model,
                    "max_tokens": 512,
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "image",
                                    "source": {
                                        "type": "base64",
                                        "media_type": "image/jpeg",
                                        "data": b64,
                                    },
                                },
                                {"type": "text", "text": prompt},
                            ],
                        }
                    ],
                },
            )
            response.raise_for_status()
            data = response.json()
            return data["content"][0]["text"]

    async def _call_vision_multi(self, images: list[bytes], prompt: str) -> str:
        content = []
        for img_bytes in images:
            b64 = base64.b64encode(img_bytes).decode("utf-8")
            content.append({
                "type": "image",
                "source": {"type": "base64", "media_type": "image/jpeg", "data": b64},
            })
        content.append({"type": "text", "text": prompt})

        async with httpx.AsyncClient(timeout=90) as client:
            response = await client.post(
                f"{self._base_url}/messages",
                headers={
                    "x-api-key": self._api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": self._model,
                    "max_tokens": 1024,
                    "messages": [{"role": "user", "content": content}],
                },
            )
            response.raise_for_status()
            data = response.json()
            return data["content"][0]["text"]

    def _parse_json(self, text: str) -> dict | list:
        text = text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1].rsplit("```", 1)[0]
        return json.loads(text)

    async def classify(self, image_bytes: bytes) -> ClassificationResult:
        try:
            text = await self._call_vision(image_bytes, CLASSIFY_PROMPT)
            data = self._parse_json(text)
            return ClassificationResult(
                category=data["category"],
                sub_category=data.get("sub_category"),
                confidence=float(data.get("confidence", 0.8)),
            )
        except Exception:
            logger.error("Claude classify failed", exc_info=True)
            return ClassificationResult(category="other", sub_category=None, confidence=0.0)

    async def assess_quality(self, image_bytes: bytes) -> QualityResult:
        try:
            text = await self._call_vision(image_bytes, QUALITY_PROMPT)
            data = self._parse_json(text)
            return QualityResult(
                quality_score=float(data.get("quality_score", 0.5)),
                is_blurry=bool(data.get("is_blurry", False)),
                is_overexposed=bool(data.get("is_overexposed", False)),
                is_underexposed=bool(data.get("is_underexposed", False)),
                is_screenshot=bool(data.get("is_screenshot", False)),
                is_invalid=bool(data.get("is_invalid", False)),
                invalid_reason=data.get("invalid_reason"),
            )
        except Exception:
            logger.error("Claude quality assessment failed", exc_info=True)
            return QualityResult(
                quality_score=0.5, is_blurry=False, is_overexposed=False,
                is_underexposed=False, is_screenshot=False, is_invalid=False,
                invalid_reason=None,
            )

    async def compute_similarity(self, image_a: bytes, image_b: bytes) -> SimilarityResult:
        try:
            text = await self._call_vision_multi([image_a, image_b], SIMILARITY_PROMPT)
            data = self._parse_json(text)
            return SimilarityResult(
                is_similar=bool(data.get("is_similar", False)),
                similarity_score=float(data.get("similarity_score", 0.0)),
            )
        except Exception:
            logger.error("Claude similarity failed", exc_info=True)
            return SimilarityResult(is_similar=False, similarity_score=0.0)

    async def pick_best(self, images: list[tuple[str, bytes]]) -> list[BestPickResult]:
        try:
            img_bytes_list = [b for _, b in images]
            text = await self._call_vision_multi(img_bytes_list, BEST_PICK_PROMPT)
            data = self._parse_json(text)
            results = []
            for item in data:
                idx = int(item["photo_index"])
                if 0 <= idx < len(images):
                    results.append(BestPickResult(
                        photo_id=images[idx][0],
                        score=float(item.get("score", 0.5)),
                        is_best=bool(item.get("is_best", False)),
                        reason=item.get("reason"),
                    ))
            return results
        except Exception:
            logger.error("Claude pick_best failed", exc_info=True)
            return [
                BestPickResult(photo_id=pid, score=0.5, is_best=(i == 0), reason=None)
                for i, (pid, _) in enumerate(images)
            ]
