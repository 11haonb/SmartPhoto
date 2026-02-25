import uuid
from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.repositories.repo import PhotoRepository, ProcessingTaskRepository
from app.services.export_service import build_zip, zip_filename

router = APIRouter()


async def _get_task_for_user(task_id: str, user_id: str, db: AsyncSession):
    task_repo = ProcessingTaskRepository(db)
    task = await task_repo.get_by_id(uuid.UUID(task_id))
    if task is None or str(task.user_id) != user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    if task.status != "completed":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Task not completed")
    return task


def _parse_date(date_str: str) -> str:
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"Invalid date: {date_str}")
    return date_str


def _streaming_response(buf, name: str, failed: int) -> StreamingResponse:
    headers = {"Content-Disposition": f'attachment; filename="{name}"'}
    if failed > 0:
        headers["X-Failed-Files"] = str(failed)
    return StreamingResponse(buf, media_type="application/zip", headers=headers)


@router.get("/by-date/{task_id}")
async def export_by_date(
    task_id: str,
    date: str = Query(..., pattern=r"^\d{4}-\d{2}-\d{2}$"),
    quality: Literal["original", "compressed"] = Query("compressed"),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    _parse_date(date)
    await _get_task_for_user(task_id, user_id, db)
    photo_repo = PhotoRepository(db)
    photos = await photo_repo.get_by_task_and_date(uuid.UUID(task_id), date)
    if not photos:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No photos found for this date")

    buf, failed = build_zip(photos, quality)
    name = zip_filename("date", date, task_id, quality)
    return _streaming_response(buf, name, failed)


@router.get("/by-category/{task_id}")
async def export_by_category(
    task_id: str,
    category: str = Query(...),
    quality: Literal["original", "compressed"] = Query("compressed"),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    await _get_task_for_user(task_id, user_id, db)
    photo_repo = PhotoRepository(db)
    photos = await photo_repo.get_by_task_and_category(uuid.UUID(task_id), category)
    if not photos:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No photos found for this category")

    buf, failed = build_zip(photos, quality)
    name = zip_filename("category", category, task_id, quality)
    return _streaming_response(buf, name, failed)


@router.get("/best/{task_id}")
async def export_best(
    task_id: str,
    quality: Literal["original", "compressed"] = Query("compressed"),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    await _get_task_for_user(task_id, user_id, db)
    photo_repo = PhotoRepository(db)
    photos = await photo_repo.get_best_by_task(uuid.UUID(task_id))
    if not photos:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No best photos found")

    buf, failed = build_zip(photos, quality)
    name = zip_filename("best", "", task_id, quality)
    return _streaming_response(buf, name, failed)
