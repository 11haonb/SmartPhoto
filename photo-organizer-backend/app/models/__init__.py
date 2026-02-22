import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    phone: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    nickname: Mapped[str | None] = mapped_column(String(128), nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    ai_configs: Mapped[list["AIConfig"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    batches: Mapped[list["Batch"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class AIConfig(Base):
    __tablename__ = "ai_configs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    provider: Mapped[str] = mapped_column(String(50), nullable=False)  # local, huggingface, tongyi, claude
    encrypted_api_key: Mapped[str | None] = mapped_column(Text, nullable=True)
    model: Mapped[str | None] = mapped_column(String(100), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    user: Mapped["User"] = relationship(back_populates="ai_configs")


class Batch(Base):
    __tablename__ = "batches"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(20), default="uploading"
    )  # uploading, uploaded, processing, completed, failed
    total_photos: Mapped[int] = mapped_column(Integer, default=0)
    uploaded_photos: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    user: Mapped["User"] = relationship(back_populates="batches")
    photos: Mapped[list["Photo"]] = relationship(back_populates="batch", cascade="all, delete-orphan")


class Photo(Base):
    __tablename__ = "photos"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    batch_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("batches.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_path: Mapped[str] = mapped_column(String(512), nullable=False)
    thumbnail_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    compressed_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    mime_type: Mapped[str] = mapped_column(String(50), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    width: Mapped[int | None] = mapped_column(Integer, nullable=True)
    height: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # EXIF data
    taken_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    camera_model: Mapped[str | None] = mapped_column(String(128), nullable=True)
    gps_latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    gps_longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    orientation: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Perceptual hash for similarity
    phash: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    batch: Mapped["Batch"] = relationship(back_populates="photos")
    analysis: Mapped["PhotoAnalysis | None"] = relationship(
        back_populates="photo", cascade="all, delete-orphan", uselist=False
    )


class PhotoAnalysis(Base):
    __tablename__ = "photo_analyses"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    photo_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("photos.id", ondelete="CASCADE"), unique=True, nullable=False
    )

    # Classification
    category: Mapped[str | None] = mapped_column(String(50), nullable=True)
    sub_category: Mapped[str | None] = mapped_column(String(50), nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Quality assessment
    quality_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    is_blurry: Mapped[bool] = mapped_column(Boolean, default=False)
    is_overexposed: Mapped[bool] = mapped_column(Boolean, default=False)
    is_underexposed: Mapped[bool] = mapped_column(Boolean, default=False)
    is_screenshot: Mapped[bool] = mapped_column(Boolean, default=False)
    is_invalid: Mapped[bool] = mapped_column(Boolean, default=False)
    invalid_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Similarity grouping
    similarity_group: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    is_best_in_group: Mapped[bool] = mapped_column(Boolean, default=False)

    # AI analysis metadata
    ai_provider: Mapped[str | None] = mapped_column(String(50), nullable=True)
    analyzed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    photo: Mapped["Photo"] = relationship(back_populates="analysis")


class ProcessingTask(Base):
    __tablename__ = "processing_tasks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    batch_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("batches.id", ondelete="CASCADE"), nullable=False
    )
    celery_task_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    status: Mapped[str] = mapped_column(
        String(20), default="pending"
    )  # pending, running, completed, failed
    current_stage: Mapped[int] = mapped_column(Integer, default=0)  # 1-5
    total_stages: Mapped[int] = mapped_column(Integer, default=5)
    current_stage_name: Mapped[str | None] = mapped_column(String(50), nullable=True)
    progress_percent: Mapped[int] = mapped_column(Integer, default=0)  # 0-100

    photos_processed: Mapped[int] = mapped_column(Integer, default=0)
    photos_total: Mapped[int] = mapped_column(Integer, default=0)

    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
