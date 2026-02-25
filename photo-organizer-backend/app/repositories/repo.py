import uuid

from sqlalchemy import cast, func, select, update
from sqlalchemy.dialects.postgresql import DATE
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import User, AIConfig, Batch, Photo, PhotoAnalysis, ProcessingTask, UserSelection


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

    async def increment_uploaded(self, batch_id: uuid.UUID) -> None:
        await self._db.execute(
            update(Batch)
            .where(Batch.id == batch_id)
            .values(
                uploaded_photos=Batch.uploaded_photos + 1,
                status=func.case(
                    (Batch.uploaded_photos + 1 >= Batch.total_photos, "uploaded"),
                    else_=Batch.status,
                ),
            )
            .execution_options(synchronize_session="fetch")
        )

    async def update_status(self, batch_id: uuid.UUID, status: str) -> None:
        batch = await self.get_by_id(batch_id)
        if batch:
            batch.status = status
            await self._db.flush()

    async def get_by_user(self, user_id: uuid.UUID) -> list[Batch]:
        result = await self._db.execute(
            select(Batch)
            .where(Batch.user_id == user_id)
            .order_by(Batch.created_at.desc())
        )
        return list(result.scalars().all())


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

    async def get_by_task_and_date(self, task_id: uuid.UUID, date_str: str) -> list[Photo]:
        date_col = func.coalesce(Photo.taken_at, Photo.created_at)
        result = await self._db.execute(
            select(Photo)
            .options(selectinload(Photo.analysis))
            .join(Batch, Photo.batch_id == Batch.id)
            .join(ProcessingTask, ProcessingTask.batch_id == Batch.id)
            .where(
                ProcessingTask.id == task_id,
                cast(date_col, DATE) == date_str,
            )
            .order_by(Photo.taken_at.asc().nullslast(), Photo.created_at.asc())
        )
        return list(result.scalars().all())

    async def get_by_task_and_category(self, task_id: uuid.UUID, category: str) -> list[Photo]:
        result = await self._db.execute(
            select(Photo)
            .options(selectinload(Photo.analysis))
            .join(Batch, Photo.batch_id == Batch.id)
            .join(ProcessingTask, ProcessingTask.batch_id == Batch.id)
            .join(PhotoAnalysis, PhotoAnalysis.photo_id == Photo.id)
            .where(
                ProcessingTask.id == task_id,
                PhotoAnalysis.category == category,
            )
        )
        return list(result.scalars().all())

    async def get_best_by_task(self, task_id: uuid.UUID) -> list[Photo]:
        result = await self._db.execute(
            select(Photo)
            .options(selectinload(Photo.analysis))
            .join(Batch, Photo.batch_id == Batch.id)
            .join(ProcessingTask, ProcessingTask.batch_id == Batch.id)
            .join(PhotoAnalysis, PhotoAnalysis.photo_id == Photo.id)
            .where(
                ProcessingTask.id == task_id,
                PhotoAnalysis.is_best_in_group == True,
            )
        )
        return list(result.scalars().all())


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

    async def unmark_best_in_group(self, similarity_group: str, task_id: uuid.UUID) -> None:
        await self._db.execute(
            update(PhotoAnalysis)
            .where(
                PhotoAnalysis.similarity_group == similarity_group,
                PhotoAnalysis.photo_id.in_(
                    select(Photo.id)
                    .join(Batch, Photo.batch_id == Batch.id)
                    .join(ProcessingTask, ProcessingTask.batch_id == Batch.id)
                    .where(ProcessingTask.id == task_id)
                )
            )
            .values(is_best_in_group=False)
            .execution_options(synchronize_session="fetch")
        )

    async def mark_best(self, photo_id: uuid.UUID) -> PhotoAnalysis | None:
        result = await self._db.execute(
            select(PhotoAnalysis)
            .where(PhotoAnalysis.photo_id == photo_id)
            .with_for_update()
        )
        analysis = result.scalar_one_or_none()
        if analysis:
            analysis.is_best_in_group = True
            await self._db.flush()
        return analysis


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


class UserSelectionRepository:
    def __init__(self, db: AsyncSession):
        self._db = db

    async def upsert(
        self,
        user_id: uuid.UUID,
        photo_id: uuid.UUID,
        similarity_group: str,
        task_id: uuid.UUID,
    ) -> UserSelection:
        result = await self._db.execute(
            select(UserSelection).where(
                UserSelection.user_id == user_id,
                UserSelection.similarity_group == similarity_group,
                UserSelection.task_id == task_id,
            )
        )
        existing = result.scalar_one_or_none()
        if existing:
            existing.photo_id = photo_id
            await self._db.flush()
            return existing

        selection = UserSelection(
            user_id=user_id,
            photo_id=photo_id,
            similarity_group=similarity_group,
            task_id=task_id,
        )
        self._db.add(selection)
        await self._db.flush()
        return selection
