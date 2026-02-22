import asyncio
import io
import logging
import uuid
from datetime import datetime, timezone

import imagehash
from PIL import Image
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.factory import create_provider
from app.core.config import settings
from app.core.database import async_session_factory
from app.core.encryption import decrypt_api_key
from app.core.storage import get_file_url
from app.models import AIConfig, Batch, Photo, PhotoAnalysis, ProcessingTask
from app.services.photo_service import extract_exif
from app.tasks.worker import celery_app

logger = logging.getLogger(__name__)

STAGE_NAMES = {
    1: "EXIF提取",
    2: "质量分析",
    3: "图片分类",
    4: "相似度分组",
    5: "最佳挑选",
}


async def _update_task_progress(
    db: AsyncSession,
    task_id: uuid.UUID,
    stage: int,
    photos_processed: int,
    photos_total: int,
) -> None:
    result = await db.execute(
        select(ProcessingTask).where(ProcessingTask.id == task_id)
    )
    task = result.scalar_one_or_none()
    if task:
        task.current_stage = stage
        task.current_stage_name = STAGE_NAMES.get(stage, "")
        task.photos_processed = photos_processed
        task.photos_total = photos_total
        task.progress_percent = int(
            ((stage - 1) / 5 + (photos_processed / max(photos_total, 1)) / 5) * 100
        )
        await db.commit()


async def _get_provider(db: AsyncSession, user_id: uuid.UUID):
    result = await db.execute(
        select(AIConfig).where(
            AIConfig.user_id == user_id,
            AIConfig.is_active == True,
        )
    )
    config = result.scalar_one_or_none()

    if config and config.provider != "local":
        api_key = None
        if config.encrypted_api_key:
            api_key = decrypt_api_key(config.encrypted_api_key)
        return create_provider(config.provider, api_key=api_key, model=config.model)

    return create_provider("local")


async def _get_photo_bytes(storage_path: str) -> bytes:
    """Download photo bytes from storage. Uses compressed version if available."""
    import boto3
    from botocore.config import Config as BotoConfig

    client = boto3.client(
        "s3",
        endpoint_url=settings.STORAGE_ENDPOINT,
        aws_access_key_id=settings.STORAGE_ACCESS_KEY,
        aws_secret_access_key=settings.STORAGE_SECRET_KEY,
        region_name=settings.STORAGE_REGION,
        config=BotoConfig(signature_version="s3v4"),
    )
    response = client.get_object(Bucket=settings.STORAGE_BUCKET, Key=storage_path)
    return response["Body"].read()


async def _run_pipeline(task_id_str: str, batch_id_str: str) -> None:
    task_id = uuid.UUID(task_id_str)
    batch_id = uuid.UUID(batch_id_str)

    async with async_session_factory() as db:
        # Mark task as running
        result = await db.execute(select(ProcessingTask).where(ProcessingTask.id == task_id))
        task = result.scalar_one()
        task.status = "running"
        task.started_at = datetime.now(timezone.utc)
        await db.commit()

        try:
            # Load photos
            result = await db.execute(select(Photo).where(Photo.batch_id == batch_id))
            photos = list(result.scalars().all())
            total = len(photos)

            provider = await _get_provider(db, task.user_id)

            # ── Stage 1: EXIF Extraction ──
            for i, photo in enumerate(photos):
                if not photo.taken_at and photo.storage_path:
                    try:
                        img_bytes = await _get_photo_bytes(photo.storage_path)
                        exif = extract_exif(img_bytes)
                        for key, value in exif.items():
                            if value is not None:
                                setattr(photo, key, value)
                    except Exception:
                        logger.warning("EXIF extraction failed for %s", photo.id)

                    # Compute pHash
                    try:
                        img_bytes = await _get_photo_bytes(
                            photo.compressed_path or photo.storage_path
                        )
                        img = Image.open(io.BytesIO(img_bytes))
                        photo.phash = str(imagehash.phash(img))
                    except Exception:
                        logger.warning("pHash computation failed for %s", photo.id)

                await _update_task_progress(db, task_id, 1, i + 1, total)

            await db.commit()

            # ── Stage 2: Quality Analysis ──
            for i, photo in enumerate(photos):
                try:
                    img_bytes = await _get_photo_bytes(
                        photo.compressed_path or photo.storage_path
                    )
                    quality = await provider.assess_quality(img_bytes)

                    analysis = PhotoAnalysis(
                        photo_id=photo.id,
                        quality_score=quality.quality_score,
                        is_blurry=quality.is_blurry,
                        is_overexposed=quality.is_overexposed,
                        is_underexposed=quality.is_underexposed,
                        is_screenshot=quality.is_screenshot,
                        is_invalid=quality.is_invalid,
                        invalid_reason=quality.invalid_reason,
                        ai_provider=provider.__class__.__name__,
                    )
                    db.add(analysis)
                except Exception:
                    logger.error("Quality analysis failed for %s", photo.id, exc_info=True)

                await _update_task_progress(db, task_id, 2, i + 1, total)

            await db.commit()

            # ── Stage 3: Classification ──
            for i, photo in enumerate(photos):
                try:
                    img_bytes = await _get_photo_bytes(
                        photo.compressed_path or photo.storage_path
                    )
                    classification = await provider.classify(img_bytes)

                    result = await db.execute(
                        select(PhotoAnalysis).where(PhotoAnalysis.photo_id == photo.id)
                    )
                    analysis = result.scalar_one_or_none()
                    if analysis:
                        analysis.category = classification.category
                        analysis.sub_category = classification.sub_category
                        analysis.confidence = classification.confidence
                        analysis.analyzed_at = datetime.now(timezone.utc)
                except Exception:
                    logger.error("Classification failed for %s", photo.id, exc_info=True)

                await _update_task_progress(db, task_id, 3, i + 1, total)

            await db.commit()

            # ── Stage 4: Similarity Grouping ──
            photos_with_hash = [p for p in photos if p.phash]
            groups: dict[str, list[Photo]] = {}
            assigned: set[uuid.UUID] = set()

            for i, photo_a in enumerate(photos_with_hash):
                if photo_a.id in assigned:
                    continue

                group_id = str(uuid.uuid4())[:8]
                group_members = [photo_a]
                assigned.add(photo_a.id)

                hash_a = imagehash.hex_to_hash(photo_a.phash)

                for photo_b in photos_with_hash[i + 1:]:
                    if photo_b.id in assigned:
                        continue
                    hash_b = imagehash.hex_to_hash(photo_b.phash)
                    distance = hash_a - hash_b
                    if distance <= 10:
                        group_members.append(photo_b)
                        assigned.add(photo_b.id)

                if len(group_members) > 1:
                    groups[group_id] = group_members
                    for member in group_members:
                        r = await db.execute(
                            select(PhotoAnalysis).where(PhotoAnalysis.photo_id == member.id)
                        )
                        analysis = r.scalar_one_or_none()
                        if analysis:
                            analysis.similarity_group = group_id

                await _update_task_progress(db, task_id, 4, i + 1, len(photos_with_hash))

            await db.commit()

            # ── Stage 5: Best Photo Selection ──
            group_count = len(groups)
            for gi, (group_id, group_photos) in enumerate(groups.items()):
                try:
                    images = []
                    for gp in group_photos:
                        img_bytes = await _get_photo_bytes(
                            gp.compressed_path or gp.storage_path
                        )
                        images.append((str(gp.id), img_bytes))

                    best_results = await provider.pick_best(images)

                    for br in best_results:
                        r = await db.execute(
                            select(PhotoAnalysis).where(
                                PhotoAnalysis.photo_id == uuid.UUID(br.photo_id)
                            )
                        )
                        analysis = r.scalar_one_or_none()
                        if analysis:
                            analysis.is_best_in_group = br.is_best
                except Exception:
                    logger.error("Best pick failed for group %s", group_id, exc_info=True)

                await _update_task_progress(db, task_id, 5, gi + 1, group_count or 1)

            await db.commit()

            # Mark task as completed
            result = await db.execute(select(ProcessingTask).where(ProcessingTask.id == task_id))
            task = result.scalar_one()
            task.status = "completed"
            task.progress_percent = 100
            task.completed_at = datetime.now(timezone.utc)

            # Update batch status
            result = await db.execute(select(Batch).where(Batch.id == batch_id))
            batch = result.scalar_one()
            batch.status = "completed"

            await db.commit()

        except Exception as e:
            logger.error("Pipeline failed for task %s: %s", task_id, e, exc_info=True)
            result = await db.execute(select(ProcessingTask).where(ProcessingTask.id == task_id))
            task = result.scalar_one_or_none()
            if task:
                task.status = "failed"
                task.error_message = str(e)
                task.completed_at = datetime.now(timezone.utc)

            result = await db.execute(select(Batch).where(Batch.id == batch_id))
            batch = result.scalar_one_or_none()
            if batch:
                batch.status = "failed"

            await db.commit()


@celery_app.task(name="run_pipeline", bind=True, max_retries=1)
def run_pipeline(self, task_id: str, batch_id: str):
    """Celery task entry point for the 5-stage processing pipeline."""
    asyncio.run(_run_pipeline(task_id, batch_id))
