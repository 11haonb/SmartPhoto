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

CLASSIFY_PROMPT = "Classify this image into: person(portrait/group/selfie), landscape(building/nature/city), food, document, screenshot, other. Return JSON only: {\"category\": \"...\", \"sub_category\": null or \"...\", \"confidence\": 0.0-1.0}"

QUALITY_PROMPT = "Assess photo quality. Return JSON: {\"quality_score\": 0.0-1.0, \"is_blurry\": bool, \"is_overexposed\": bool, \"is_underexposed\": bool, \"is_screenshot\": bool, \"is_invalid\": bool, \"invalid_reason\": null or \"...\"}"


class HuggingFaceProvider(AIProvider):
    """HuggingFace Inference API provider."""

    def __init__(self, api_key: str | None = None, model: str = "Salesforce/blip2-opt-2.7b"):
        self._api_key = api_key or ""
        self._model = model
        self._base_url = "https://api-inference.huggingface.co/models"

    async def _call_model(self, image_bytes: bytes, prompt: str) -> str:
        headers = {}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"

        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                f"{self._base_url}/{self._model}",
                headers=headers,
                json={
                    "inputs": {
                        "image": base64.b64encode(image_bytes).decode("utf-8"),
                        "text": prompt,
                    },
                },
            )
            response.raise_for_status()
            data = response.json()
            if isinstance(data, list) and data:
                return data[0].get("generated_text", "")
            return str(data)

    def _parse_json_safe(self, text: str) -> dict:
        text = text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1].rsplit("```", 1)[0]
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return {}

    async def classify(self, image_bytes: bytes) -> ClassificationResult:
        try:
            text = await self._call_model(image_bytes, CLASSIFY_PROMPT)
            data = self._parse_json_safe(text)
            if data.get("category"):
                return ClassificationResult(
                    category=data["category"],
                    sub_category=data.get("sub_category"),
                    confidence=float(data.get("confidence", 0.6)),
                )
        except Exception:
            logger.error("HuggingFace classify failed, falling back to local", exc_info=True)

        from app.ai.providers.local_provider import LocalProvider
        return await LocalProvider().classify(image_bytes)

    async def assess_quality(self, image_bytes: bytes) -> QualityResult:
        # Fallback to local analysis for quality since HF free tier is limited
        from app.ai.providers.local_provider import LocalProvider

        local = LocalProvider()
        return await local.assess_quality(image_bytes)

    async def compute_similarity(self, image_a: bytes, image_b: bytes) -> SimilarityResult:
        from app.ai.providers.local_provider import LocalProvider

        local = LocalProvider()
        return await local.compute_similarity(image_a, image_b)

    async def pick_best(self, images: list[tuple[str, bytes]]) -> list[BestPickResult]:
        from app.ai.providers.local_provider import LocalProvider

        local = LocalProvider()
        return await local.pick_best(images)
