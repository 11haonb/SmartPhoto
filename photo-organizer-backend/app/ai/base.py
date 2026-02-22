from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class ClassificationResult:
    category: str  # person, landscape, food, document, screenshot, other
    sub_category: str | None  # portrait, group, selfie, building, nature, etc.
    confidence: float  # 0.0 - 1.0


@dataclass
class QualityResult:
    quality_score: float  # 0.0 - 1.0
    is_blurry: bool
    is_overexposed: bool
    is_underexposed: bool
    is_screenshot: bool
    is_invalid: bool
    invalid_reason: str | None


@dataclass
class SimilarityResult:
    is_similar: bool
    similarity_score: float  # 0.0 - 1.0


@dataclass
class BestPickResult:
    photo_id: str
    score: float  # 0.0 - 1.0
    is_best: bool
    reason: str | None


class AIProvider(ABC):
    """Base class for all AI providers. Implements Strategy pattern."""

    @abstractmethod
    async def classify(self, image_bytes: bytes) -> ClassificationResult:
        """Classify image into categories."""

    @abstractmethod
    async def assess_quality(self, image_bytes: bytes) -> QualityResult:
        """Assess image quality (blur, exposure, screenshot detection)."""

    @abstractmethod
    async def compute_similarity(self, image_a: bytes, image_b: bytes) -> SimilarityResult:
        """Compute similarity between two images."""

    @abstractmethod
    async def pick_best(self, images: list[tuple[str, bytes]]) -> list[BestPickResult]:
        """Pick the best photo from a group of similar images.
        Args: list of (photo_id, image_bytes) tuples
        Returns: list of BestPickResult with scores
        """
