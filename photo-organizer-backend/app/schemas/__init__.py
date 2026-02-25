from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


# ── Auth (Phone + SMS) ──
class SendSmsCodeRequest(BaseModel):
    phone: str = Field(..., pattern=r"^1[3-9]\d{9}$", description="China mainland phone number")


class SendSmsCodeResponse(BaseModel):
    message: str = "Verification code sent"


class PhoneLoginRequest(BaseModel):
    phone: str = Field(..., pattern=r"^1[3-9]\d{9}$")
    code: str = Field(..., min_length=4, max_length=8)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: UUID


# ── User ──
class UserResponse(BaseModel):
    id: UUID
    phone: str
    nickname: str | None
    avatar_url: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class UserUpdateRequest(BaseModel):
    nickname: str | None = Field(None, max_length=128)
    avatar_url: str | None = Field(None, max_length=512)


# ── AI Config ──
class AIProviderInfo(BaseModel):
    provider: str
    name: str
    description: str
    requires_api_key: bool
    free_tier: str | None
    accuracy: str


class AIConfigCreate(BaseModel):
    provider: str = Field(..., pattern="^(local|clip|huggingface|tongyi|claude)$")
    api_key: str | None = None
    model: str | None = None


class AIConfigResponse(BaseModel):
    id: UUID
    provider: str
    has_api_key: bool
    model: str | None
    is_active: bool

    model_config = {"from_attributes": True}


# ── Batch ──
class BatchCreateRequest(BaseModel):
    total_photos: int = Field(..., ge=1, le=100)


class BatchResponse(BaseModel):
    id: UUID
    status: str
    total_photos: int
    uploaded_photos: int
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Photo ──
class PhotoResponse(BaseModel):
    id: UUID
    original_filename: str
    thumbnail_url: str | None = None
    compressed_url: str | None = None
    mime_type: str
    file_size: int
    width: int | None
    height: int | None
    taken_at: datetime | None
    camera_model: str | None
    gps_latitude: float | None
    gps_longitude: float | None
    created_at: datetime

    model_config = {"from_attributes": True}


class PhotoUploadResponse(BaseModel):
    id: UUID
    batch_id: UUID
    original_filename: str
    thumbnail_url: str | None


# ── Photo Analysis ──
class PhotoAnalysisResponse(BaseModel):
    photo_id: UUID
    category: str | None
    sub_category: str | None
    confidence: float | None
    quality_score: float | None
    is_blurry: bool
    is_overexposed: bool
    is_underexposed: bool
    is_screenshot: bool
    is_invalid: bool
    invalid_reason: str | None
    similarity_group: str | None
    is_best_in_group: bool
    ai_provider: str | None
    analyzed_at: datetime | None

    model_config = {"from_attributes": True}


class PhotoDetailResponse(BaseModel):
    photo: PhotoResponse
    analysis: PhotoAnalysisResponse | None


# ── Processing Task ──
class OrganizeStartRequest(BaseModel):
    batch_id: UUID


class OrganizeStartResponse(BaseModel):
    task_id: UUID
    status: str


class ProcessingTaskStatusResponse(BaseModel):
    id: UUID
    status: str
    current_stage: int
    total_stages: int
    current_stage_name: str | None
    progress_percent: int
    photos_processed: int
    photos_total: int
    error_message: str | None
    started_at: datetime | None
    completed_at: datetime | None

    model_config = {"from_attributes": True}


# ── Organize Results ──
class TimelineGroup(BaseModel):
    date: str
    photos: list[PhotoResponse]


class CategoryGroup(BaseModel):
    category: str
    sub_category: str | None
    count: int
    photos: list[PhotoResponse]


class SimilarityGroup(BaseModel):
    group_id: str
    photos: list[PhotoDetailResponse]
    best_photo_id: UUID | None


class OrganizeResultsResponse(BaseModel):
    task_id: UUID
    timeline: list[TimelineGroup]
    categories: list[CategoryGroup]
    invalid_photos: list[PhotoDetailResponse]
    similarity_groups: list[SimilarityGroup]


# ── Settings ──
class UserSettingsResponse(BaseModel):
    ai_config: AIConfigResponse | None
    available_providers: list[AIProviderInfo]


class UserSettingsUpdate(BaseModel):
    ai_config: AIConfigCreate | None = None


# ── Mark Best ──
class MarkBestRequest(BaseModel):
    task_id: UUID


class MarkBestResponse(BaseModel):
    photo_id: UUID
    similarity_group: str
    is_best_in_group: bool
