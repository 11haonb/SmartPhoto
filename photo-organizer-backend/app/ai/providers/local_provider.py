import io
import logging

import numpy as np
from PIL import Image, ImageFilter

from app.ai.base import (
    AIProvider,
    BestPickResult,
    ClassificationResult,
    QualityResult,
    SimilarityResult,
)

logger = logging.getLogger(__name__)

# Common screenshot resolutions
SCREENSHOT_RESOLUTIONS = {
    (1170, 2532), (1284, 2778), (1125, 2436),  # iPhone
    (1080, 1920), (1080, 2340), (1080, 2400),  # Android
    (1440, 2560), (1440, 3200),  # Android high-res
    (2048, 2732), (1668, 2388), (1620, 2160),  # iPad
}


class LocalProvider(AIProvider):
    """Offline image analysis using Pillow + NumPy. No API key needed."""

    async def classify(self, image_bytes: bytes) -> ClassificationResult:
        img = Image.open(io.BytesIO(image_bytes))

        # Basic heuristic classification
        w, h = img.size
        aspect = w / h if h > 0 else 1

        # Screenshot detection by resolution
        if (w, h) in SCREENSHOT_RESOLUTIONS or (h, w) in SCREENSHOT_RESOLUTIONS:
            return ClassificationResult(
                category="screenshot", sub_category=None, confidence=0.7
            )

        # Document detection (mostly white/light background)
        arr = np.array(img.convert("L"))
        white_ratio = np.mean(arr > 200)
        if white_ratio > 0.7:
            return ClassificationResult(
                category="document", sub_category=None, confidence=0.5
            )

        # Landscape heuristic (wide aspect ratio)
        if aspect > 1.5:
            return ClassificationResult(
                category="landscape", sub_category=None, confidence=0.4
            )

        # Portrait heuristic (tall aspect ratio)
        if aspect < 0.7:
            return ClassificationResult(
                category="person", sub_category="portrait", confidence=0.3
            )

        return ClassificationResult(
            category="other", sub_category=None, confidence=0.2
        )

    async def assess_quality(self, image_bytes: bytes) -> QualityResult:
        img = Image.open(io.BytesIO(image_bytes))
        arr = np.array(img.convert("L"), dtype=np.float64)
        w, h = img.size

        # Blur detection using Laplacian variance
        laplacian = np.array([[0, 1, 0], [1, -4, 1], [0, 1, 0]])
        from scipy.signal import convolve2d

        lap = convolve2d(arr, laplacian, mode="same", boundary="symm")
        blur_score = float(np.var(lap))
        is_blurry = blur_score < 100

        # Exposure analysis
        mean_brightness = float(np.mean(arr))
        is_overexposed = mean_brightness > 230
        is_underexposed = mean_brightness < 30

        # Screenshot detection
        is_screenshot = (w, h) in SCREENSHOT_RESOLUTIONS or (h, w) in SCREENSHOT_RESOLUTIONS

        # Quality score (0-1)
        score = 0.5
        if not is_blurry:
            score += 0.2
        if not is_overexposed and not is_underexposed:
            score += 0.2
        if not is_screenshot:
            score += 0.1

        # Normalize blur_score contribution
        blur_norm = min(blur_score / 500, 1.0)
        score = score * 0.7 + blur_norm * 0.3

        is_invalid = is_blurry and blur_score < 30

        return QualityResult(
            quality_score=round(min(score, 1.0), 3),
            is_blurry=is_blurry,
            is_overexposed=is_overexposed,
            is_underexposed=is_underexposed,
            is_screenshot=is_screenshot,
            is_invalid=is_invalid,
            invalid_reason="Image is too blurry" if is_invalid else None,
        )

    async def compute_similarity(self, image_a: bytes, image_b: bytes) -> SimilarityResult:
        import imagehash

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
            results.append(
                BestPickResult(
                    photo_id=photo_id,
                    score=quality.quality_score,
                    is_best=False,
                    reason=None,
                )
            )
            if quality.quality_score > best_score:
                best_score = quality.quality_score
                best_id = photo_id

        return [
            BestPickResult(
                photo_id=r.photo_id,
                score=r.score,
                is_best=(r.photo_id == best_id),
                reason="Highest quality score" if r.photo_id == best_id else None,
            )
            for r in results
        ]
