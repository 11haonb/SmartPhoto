import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import User, AIConfig, Batch, Photo, PhotoAnalysis, ProcessingTask


class UserRepository:
    def __init__(self, db: AsyncSession):
        self._db = db

    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        result = await self._db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_by_phone(self, phone: str) -> User | None:
        result = await self._db.execute(select(User).where(User.phone == phone))
        return result.scalar_one_or_none()

    async def create(self, phone: str) -> User:
        user = User(phone=phone)
        self._db.add(user)
        await self._db.flush()
        return user

    async def update(self, user_id: uuid.UUID, **kwargs) -> User | None:
        user = await self.get_by_id(user_id)
        if user is None:
            return None
        for key, value in kwargs.items():
            setattr(user, key, value)
        await self._db.flush()
        return user


class AIConfigRepository:
    def __init__(self, db: AsyncSession):
        self._db = db

    async def get_active_by_user(self, user_id: uuid.UUID) -> AIConfig | None:
        result = await self._db.execute(
            select(AIConfig).where(
                AIConfig.user_id == user_id,
                AIConfig.is_active == True,
            )
        )
        return result.scalar_one_or_none()

    async def upsert(self, user_id: uuid.UUID, provider: str, encrypted_api_key: str | None, model: str | None) -> AIConfig:
        existing = await self.get_active_by_user(user_id)
        if existing:
            existing.provider = provider
            existing.encrypted_api_key = encrypted_api_key
            existing.model = model
            await self._db.flush()
            return existing

        config = AIConfig(
            user_id=user_id,
            provider=provider,
            encrypted_api_key=encrypted_api_key,
            model=model,
        )
        self._db.add(config)
        await self._db.flush()
        return config


class BatchRepository:
    def __init__(self, db: AsyncSession):
        self._db = db

    async def create(self, user_id: uuid.UUID, total_photos: int) -> Batch:
        batch = Batch(user_id=user_id, total_photos=total_photos)
        self._db.add(batch)
        await self._db.flush()
        return batch

    async def get_by_id(self, batch_id: uuid.UUID) -> Batch | None:
        result = await self._db.execute(
            select(Batch).where(Batch.id == batch_id)
        )
        return result.scalar_one_or_none()

    async def increment_uploaded(self, batch_id: uuid.UUID) -> Batch | None:
        batch = await self.get_by_id(batch_id)
        if batch is None:
            return None
        batch.uploaded_photos = batch.uploaded_photos + 1
        if batch.uploaded_photos >= batch.total_photos:
            batch.status = "uploaded"
        await self._db.flush()
        return batch

    async def update_status(self, batch_id: uuid.UUID, status: str) -> None:
        batch = await self.get_by_id(batch_id)
        if batch:
            batch.status = status
            await self._db.flush()


class PhotoRepository:
    def __init__(self, db: AsyncSession):
        self._db = db

    async def create(self, **kwargs) -> Photo:
        photo = Photo(**kwargs)
        self._db.add(photo)
        await self._db.flush()
        return photo

    async def get_by_id(self, photo_id: uuid.UUID) -> Photo | None:
        result = await self._db.execute(
            select(Photo)
            .options(selectinload(Photo.analysis))
            .where(Photo.id == photo_id)
        )
        return result.scalar_one_or_none()

    async def get_by_batch(self, batch_id: uuid.UUID) -> list[Photo]:
        result = await self._db.execute(
            select(Photo)
            .options(selectinload(Photo.analysis))
            .where(Photo.batch_id == batch_id)
            .order_by(Photo.taken_at.asc().nullslast(), Photo.created_at.asc())
        )
        return list(result.scalars().all())

    async def delete(self, photo_id: uuid.UUID) -> bool:
        photo = await self.get_by_id(photo_id)
        if photo is None:
            return False
        await self._db.delete(photo)
        await self._db.flush()
        return True

    async def update(self, photo_id: uuid.UUID, **kwargs) -> Photo | None:
        photo = await self.get_by_id(photo_id)
        if photo is None:
            return None
        for key, value in kwargs.items():
            setattr(photo, key, value)
        await self._db.flush()
        return photo


class PhotoAnalysisRepository:
    def __init__(self, db: AsyncSession):
        self._db = db

    async def create_or_update(self, photo_id: uuid.UUID, **kwargs) -> PhotoAnalysis:
        result = await self._db.execute(
            select(PhotoAnalysis).where(PhotoAnalysis.photo_id == photo_id)
        )
        existing = result.scalar_one_or_none()

        if existing:
            for key, value in kwargs.items():
                setattr(existing, key, value)
            await self._db.flush()
            return existing

        analysis = PhotoAnalysis(photo_id=photo_id, **kwargs)
        self._db.add(analysis)
        await self._db.flush()
        return analysis

    async def get_by_batch(self, batch_id: uuid.UUID) -> list[PhotoAnalysis]:
        result = await self._db.execute(
            select(PhotoAnalysis)
            .join(Photo)
            .where(Photo.batch_id == batch_id)
        )
        return list(result.scalars().all())


class ProcessingTaskRepository:
    def __init__(self, db: AsyncSession):
        self._db = db

    async def create(self, user_id: uuid.UUID, batch_id: uuid.UUID, photos_total: int) -> ProcessingTask:
        task = ProcessingTask(
            user_id=user_id,
            batch_id=batch_id,
            photos_total=photos_total,
        )
        self._db.add(task)
        await self._db.flush()
        return task

    async def get_by_id(self, task_id: uuid.UUID) -> ProcessingTask | None:
        result = await self._db.execute(
            select(ProcessingTask).where(ProcessingTask.id == task_id)
        )
        return result.scalar_one_or_none()

    async def update(self, task_id: uuid.UUID, **kwargs) -> ProcessingTask | None:
        task = await self.get_by_id(task_id)
        if task is None:
            return None
        for key, value in kwargs.items():
            setattr(task, key, value)
        await self._db.flush()
        return task
