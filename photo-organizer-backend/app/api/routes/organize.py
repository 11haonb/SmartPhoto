import math
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.repositories.repo import (
    BatchRepository,
    PhotoRepository,
    ProcessingTaskRepository,
)
from app.schemas import (
    OrganizeStartRequest,
    OrganizeStartResponse,
    ProcessingTaskStatusResponse,
    OrganizeResultsResponse,
    TimelineGroup,
    CategoryGroup,
    SimilarityGroup,
    PhotoResponse,
    PhotoDetailResponse,
    PhotoAnalysisResponse,
)
from app.services.photo_service import get_photo_urls

router = APIRouter()


@router.post("/start", response_model=OrganizeStartResponse)
async def start_organize(
    request: OrganizeStartRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    batch_repo = BatchRepository(db)
    batch = await batch_repo.get_by_id(request.batch_id)
    if batch is None or str(batch.user_id) != user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Batch not found")

    if batch.status not in ("uploaded", "completed", "failed"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Batch is still {batch.status}, cannot start organizing",
        )

    photo_repo = PhotoRepository(db)
    photos = await photo_repo.get_by_batch(request.batch_id)
    if not photos:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No photos in batch")

    task_repo = ProcessingTaskRepository(db)
    task = await task_repo.create(
        user_id=uuid.UUID(user_id),
        batch_id=request.batch_id,
        photos_total=len(photos),
    )

    await batch_repo.update_status(request.batch_id, "processing")

    from app.tasks.pipeline import run_pipeline

    celery_task = run_pipeline.delay(str(task.id), str(request.batch_id))
    await task_repo.update(task.id, celery_task_id=celery_task.id)

    return OrganizeStartResponse(task_id=task.id, status="pending")


@router.get("/status/{task_id}", response_model=ProcessingTaskStatusResponse)
async def get_organize_status(
    task_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    task_repo = ProcessingTaskRepository(db)
    task = await task_repo.get_by_id(uuid.UUID(task_id))
    if task is None or str(task.user_id) != user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return task


@router.get("/results/{task_id}", response_model=OrganizeResultsResponse)
async def get_organize_results(
    task_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    task_repo = ProcessingTaskRepository(db)
    task = await task_repo.get_by_id(uuid.UUID(task_id))
    if task is None or str(task.user_id) != user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    if task.status != "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Task is {task.status}, results not available yet",
        )

    photo_repo = PhotoRepository(db)
    all_photos = await photo_repo.get_by_batch(task.batch_id)
    total_photos = len(all_photos)
    total_pages = max(1, math.ceil(total_photos / page_size))
    offset = (page - 1) * page_size
    photos = all_photos[offset: offset + page_size]

    timeline_map: dict[str, list] = {}
    categories_map: dict[str, dict] = {}
    invalid_photos: list[PhotoDetailResponse] = []
    similarity_map: dict[str, dict] = {}

    for photo in photos:
        urls = get_photo_urls(photo)
        photo_resp = PhotoResponse.model_validate(photo)
        photo_resp.thumbnail_url = urls["thumbnail_url"]
        photo_resp.compressed_url = urls["compressed_url"]

        analysis_resp = None
        if photo.analysis:
            analysis_resp = PhotoAnalysisResponse.model_validate(photo.analysis)

        detail = PhotoDetailResponse(photo=photo_resp, analysis=analysis_resp)

        date_key = (photo.taken_at or photo.created_at).strftime("%Y-%m-%d")
        timeline_map.setdefault(date_key, []).append(photo_resp)

        if photo.analysis:
            if photo.analysis.category:
                cat_key = f"{photo.analysis.category}:{photo.analysis.sub_category or ''}"
                if cat_key not in categories_map:
                    categories_map[cat_key] = {
                        "category": photo.analysis.category,
                        "sub_category": photo.analysis.sub_category,
                        "photos": [],
                    }
                categories_map[cat_key]["photos"].append(photo_resp)

            if photo.analysis.is_invalid:
                invalid_photos.append(detail)

            if photo.analysis.similarity_group:
                group_id = photo.analysis.similarity_group
                if group_id not in similarity_map:
                    similarity_map[group_id] = {"photos": [], "best_photo_id": None}
                similarity_map[group_id]["photos"].append(detail)
                if photo.analysis.is_best_in_group:
                    similarity_map[group_id]["best_photo_id"] = photo.id

    timeline = [
        TimelineGroup(date=date, photos=photos_list)
        for date, photos_list in sorted(timeline_map.items(), reverse=True)
    ]
    categories = [
        CategoryGroup(
            category=data["category"],
            sub_category=data["sub_category"],
            count=len(data["photos"]),
            photos=data["photos"],
        )
        for data in categories_map.values()
    ]
    similarity_groups = [
        SimilarityGroup(
            group_id=group_id,
            photos=data["photos"],
            best_photo_id=data["best_photo_id"],
        )
        for group_id, data in similarity_map.items()
    ]

    return OrganizeResultsResponse(
        task_id=uuid.UUID(task_id),
        timeline=timeline,
        categories=categories,
        invalid_photos=invalid_photos,
        similarity_groups=similarity_groups,
        total_photos=total_photos,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )
