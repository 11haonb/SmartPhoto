import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.encryption import encrypt_api_key
from app.core.security import get_current_user_id
from app.repositories.repo import AIConfigRepository
from app.schemas import (
    AIConfigCreate,
    AIConfigResponse,
    AIProviderInfo,
    UserSettingsResponse,
    UserSettingsUpdate,
)

router = APIRouter()

AVAILABLE_PROVIDERS = [
    AIProviderInfo(
        provider="local",
        name="本地离线分析",
        description="使用 Pillow + NumPy 进行基础图像分析，无需网络和 API Key",
        requires_api_key=False,
        free_tier="无限制",
        accuracy="基础",
    ),
    AIProviderInfo(
        provider="clip",
        name="CLIP 本地推理",
        description="使用 OpenAI CLIP 模型进行零样本图像分类，本地运行，无需 API Key",
        requires_api_key=False,
        free_tier="无限制",
        accuracy="中等",
    ),
    AIProviderInfo(
        provider="huggingface",
        name="HuggingFace",
        description="使用 HuggingFace 免费推理 API，适合轻度使用",
        requires_api_key=False,
        free_tier="30K 次/月",
        accuracy="中等",
    ),
    AIProviderInfo(
        provider="tongyi",
        name="通义千问 VL",
        description="阿里云通义千问视觉语言模型，国内访问快，准确度高",
        requires_api_key=True,
        free_tier="有免费额度",
        accuracy="高",
    ),
    AIProviderInfo(
        provider="claude",
        name="Claude Vision",
        description="Anthropic Claude 视觉分析，准确度最高",
        requires_api_key=True,
        free_tier=None,
        accuracy="最高",
    ),
]


@router.get("", response_model=UserSettingsResponse)
async def get_settings(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    repo = AIConfigRepository(db)
    config = await repo.get_active_by_user(uuid.UUID(user_id))

    ai_config_resp = None
    if config:
        ai_config_resp = AIConfigResponse(
            id=config.id,
            provider=config.provider,
            has_api_key=config.encrypted_api_key is not None,
            model=config.model,
            is_active=config.is_active,
        )

    return UserSettingsResponse(
        ai_config=ai_config_resp,
        available_providers=AVAILABLE_PROVIDERS,
    )


@router.put("", response_model=UserSettingsResponse)
async def update_settings(
    request: UserSettingsUpdate,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    repo = AIConfigRepository(db)

    if request.ai_config:
        encrypted_key = None
        if request.ai_config.api_key:
            encrypted_key = encrypt_api_key(request.ai_config.api_key)

        config = await repo.upsert(
            user_id=uuid.UUID(user_id),
            provider=request.ai_config.provider,
            encrypted_api_key=encrypted_key,
            model=request.ai_config.model,
        )

    config = await repo.get_active_by_user(uuid.UUID(user_id))
    ai_config_resp = None
    if config:
        ai_config_resp = AIConfigResponse(
            id=config.id,
            provider=config.provider,
            has_api_key=config.encrypted_api_key is not None,
            model=config.model,
            is_active=config.is_active,
        )

    return UserSettingsResponse(
        ai_config=ai_config_resp,
        available_providers=AVAILABLE_PROVIDERS,
    )


@router.get("/ai-providers", response_model=list[AIProviderInfo])
async def get_ai_providers():
    return AVAILABLE_PROVIDERS
