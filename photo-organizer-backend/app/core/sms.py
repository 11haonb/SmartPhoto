import logging
import secrets
import string

import redis.asyncio as redis

from app.core.config import settings

logger = logging.getLogger(__name__)

_redis_client: redis.Redis | None = None


async def get_redis() -> redis.Redis:
    global _redis_client
    if _redis_client is None:
        pool = redis.ConnectionPool.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            max_connections=20,
        )
        _redis_client = redis.Redis(connection_pool=pool)
    return _redis_client


def _generate_code(length: int = 6) -> str:
    return "".join(secrets.choice(string.digits) for _ in range(length))


async def send_sms_code(phone: str) -> str:
    r = await get_redis()

    rate_key = f"sms:rate:{phone}"
    if await r.exists(rate_key):
        raise ValueError("SMS sent too frequently, please try again later")

    if settings.APP_ENV == "development":
        code = "888888"
    else:
        code = _generate_code(settings.SMS_CODE_LENGTH)

    code_key = f"sms:code:{phone}"
    await r.setex(code_key, settings.SMS_CODE_EXPIRE_SECONDS, code)
    await r.setex(rate_key, settings.SMS_RATE_LIMIT_SECONDS, "1")

    if settings.APP_ENV == "development":
        logger.info("DEV MODE - SMS code for %s: %s (fixed code)", phone, code)
    else:
        await _send_aliyun_sms(phone, code)

    return code


async def verify_sms_code(phone: str, code: str) -> bool:
    r = await get_redis()
    code_key = f"sms:code:{phone}"
    stored_code = await r.get(code_key)

    if stored_code is None:
        return False

    if stored_code != code:
        return False

    await r.delete(code_key)
    return True


async def _send_aliyun_sms(phone: str, code: str) -> None:
    try:
        from alibabacloud_dysmsapi20170525.client import Client
        from alibabacloud_tea_openapi.models import Config

        config = Config(
            access_key_id=settings.SMS_ACCESS_KEY_ID,
            access_key_secret=settings.SMS_ACCESS_KEY_SECRET,
            endpoint="dysmsapi.aliyuncs.com",
        )
        client = Client(config)

        from alibabacloud_dysmsapi20170525.models import SendSmsRequest
        import json

        request = SendSmsRequest(
            phone_numbers=phone,
            sign_name=settings.SMS_SIGN_NAME,
            template_code=settings.SMS_TEMPLATE_CODE,
            template_param=json.dumps({"code": code}),
        )
        response = client.send_sms(request)
        if response.body.code != "OK":
            logger.error("SMS send failed: %s", response.body.message)
            raise RuntimeError(f"SMS send failed: {response.body.message}")
    except ImportError:
        logger.warning("Aliyun SMS SDK not installed, skipping real SMS send")
        logger.info("SMS code for %s: %s", phone, code)
