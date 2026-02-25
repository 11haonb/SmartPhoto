from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from app.core.config import settings
from app.api.routes import auth, photos, organize, settings as settings_routes
from app.api.routes import export


def create_app() -> FastAPI:
    application = FastAPI(
        title=settings.APP_NAME,
        version="1.0.0",
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=(
            ["*"] if settings.CORS_ORIGINS == "*"
            else [o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()]
        ),
        allow_credentials=settings.CORS_ORIGINS != "*",
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @application.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=422,
            content={"detail": exc.errors()},
        )

    @application.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        import logging
        logging.getLogger(__name__).error(
            "Unhandled exception %s %s: %s", request.method, request.url.path, exc, exc_info=True
        )
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"},
        )

    application.include_router(
        auth.router,
        prefix="/api/v1/auth",
        tags=["auth"],
    )
    application.include_router(
        photos.router,
        prefix="/api/v1/photos",
        tags=["photos"],
    )
    application.include_router(
        organize.router,
        prefix="/api/v1/organize",
        tags=["organize"],
    )
    application.include_router(
        settings_routes.router,
        prefix="/api/v1/settings",
        tags=["settings"],
    )
    application.include_router(
        export.router,
        prefix="/api/v1/export",
        tags=["export"],
    )

    @application.get("/health")
    async def health_check():
        from sqlalchemy import text
        from app.core.database import engine
        from app.core.sms import get_redis

        checks: dict[str, str] = {}

        try:
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            checks["db"] = "ok"
        except Exception:
            checks["db"] = "error"

        try:
            r = await get_redis()
            await r.ping()
            checks["redis"] = "ok"
        except Exception:
            checks["redis"] = "error"

        overall = "ok" if all(v == "ok" for v in checks.values()) else "degraded"
        return {"status": overall, **checks}

    return application


app = create_app()
