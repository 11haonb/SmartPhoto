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

CLASSIFY_PROMPT = "将这张图片分为以下类别之一：person(子类:portrait/group/selfie), landscape(子类:building/nature/city), food, document, screenshot, other。仅返回JSON: {\"category\": \"...\", \"sub_category\": \"...\"或null, \"confidence\": 0.0-1.0}"

QUALITY_PROMPT = "评估这张照片的质量。检查: 模糊、过曝、欠曝、是否截图。仅返回JSON: {\"quality_score\": 0.0-1.0, \"is_blurry\": bool, \"is_overexposed\": bool, \"is_underexposed\": bool, \"is_screenshot\": bool, \"is_invalid\": bool, \"invalid_reason\": \"...\"或null}"


class TongyiProvider(AIProvider):
    """Tongyi Qianwen VL (通义千问视觉语言模型) provider."""

    def __init__(self, api_key: str, model: str = "qwen-vl-max"):
        self._api_key = api_key
        self._model = model

    async def _call_vision(self, image_bytes: bytes, prompt: str) -> str:
        b64 = base64.b64encode(image_bytes).decode("utf-8")
        url = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"

        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                url,
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self._model,
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "image_url",
                                    "image_url": {"url": f"data:image/jpeg;base64,{b64}"},
                                },
                                {"type": "text", "text": prompt},
                            ],
                        }
                    ],
                },
            )
            response.raise_for_status()
            data = response.json()
            usage = data.get("usage", {})
            logger.info(
                "Tongyi usage model=%s prompt_tokens=%s completion_tokens=%s total_tokens=%s",
                self._model,
                usage.get("prompt_tokens"),
                usage.get("completion_tokens"),
                usage.get("total_tokens"),
            )
            return data["choices"][0]["message"]["content"]

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
            logger.error("Tongyi classify failed", exc_info=True)
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
            logger.error("Tongyi quality assessment failed", exc_info=True)
            return QualityResult(
                quality_score=0.5, is_blurry=False, is_overexposed=False,
                is_underexposed=False, is_screenshot=False, is_invalid=False,
                invalid_reason=None,
            )

    async def compute_similarity(self, image_a: bytes, image_b: bytes) -> SimilarityResult:
        # Tongyi VL supports multi-image, but use pHash as primary for similarity
        import imagehash
        from PIL import Image
        import io

        img_a = Image.open(io.BytesIO(image_a))
        img_b = Image.open(io.BytesIO(image_b))
        hash_a = imagehash.phash(img_a)
        hash_b = imagehash.phash(img_b)
        distance = hash_a - hash_b
        similarity = max(0, 1 - distance / 64)

        return SimilarityResult(
            is_similar=distance <= 10,
            similarity_score=round(similarity, 3),
        )

    async def pick_best(self, images: list[tuple[str, bytes]]) -> list[BestPickResult]:
        results = []
        best_score = -1
        best_id = None

        for photo_id, img_bytes in images:
            quality = await self.assess_quality(img_bytes)
            results.append(BestPickResult(
                photo_id=photo_id,
                score=quality.quality_score,
                is_best=False,
                reason=None,
            ))
            if quality.quality_score > best_score:
                best_score = quality.quality_score
                best_id = photo_id

        return [
            BestPickResult(
                photo_id=r.photo_id,
                score=r.score,
                is_best=(r.photo_id == best_id),
                reason="Best quality in group" if r.photo_id == best_id else None,
            )
            for r in results
        ]
