from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.routes import auth, photos, organize, settings as settings_routes


def create_app() -> FastAPI:
    application = FastAPI(
        title=settings.APP_NAME,
        version="1.0.0",
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
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

    @application.get("/health")
    async def health_check():
        return {"status": "ok"}

    return application


app = create_app()
