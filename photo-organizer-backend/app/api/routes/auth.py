from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import create_access_token
from app.core.sms import send_sms_code, verify_sms_code
from app.repositories.repo import UserRepository
from app.schemas import (
    SendSmsCodeRequest,
    SendSmsCodeResponse,
    PhoneLoginRequest,
    TokenResponse,
)

router = APIRouter()


@router.post("/send-code", response_model=SendSmsCodeResponse)
async def send_verification_code(
    request: SendSmsCodeRequest,
):
    try:
        await send_sms_code(request.phone)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send SMS",
        )
    return SendSmsCodeResponse()


@router.post("/login", response_model=TokenResponse)
async def phone_login(
    request: PhoneLoginRequest,
    db: AsyncSession = Depends(get_db),
):
    is_valid = await verify_sms_code(request.phone, request.code)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired verification code",
        )

    repo = UserRepository(db)
    user = await repo.get_by_phone(request.phone)
    if user is None:
        user = await repo.create(request.phone)

    token = create_access_token(str(user.id))
    return TokenResponse(access_token=token, user_id=user.id)
