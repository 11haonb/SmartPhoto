import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.core.storage import delete_file
from app.repositories.repo import (
    BatchRepository,
    PhotoRepository,
    PhotoAnalysisRepository,
    UserRepository,
    UserSelectionRepository,
)
from app.schemas import (
    BatchCreateRequest,
    BatchListResponse,
    BatchResponse,
    PhotoDetailResponse,
    PhotoResponse,
    PhotoUploadResponse,
    PhotoAnalysisResponse,
    MarkBestRequest,
    MarkBestResponse,
    UserResponse,
    UserUpdateRequest,
)
from app.services.photo_service import get_photo_urls, process_upload

router = APIRouter()


# ── User ──

@router.get("/me", response_model=UserResponse)
async def get_me(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    repo = UserRepository(db)
    user = await repo.get_by_id(uuid.UUID(user_id))
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@router.put("/me", response_model=UserResponse)
async def update_me(
    request: UserUpdateRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    repo = UserRepository(db)
    user = await repo.update(uuid.UUID(user_id), **request.model_dump(exclude_none=True))
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


# ── Batch ──

@router.get("/batches", response_model=list[BatchListResponse])
async def list_batches(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    repo = BatchRepository(db)
    return await repo.get_by_user(uuid.UUID(user_id))


@router.post("/batch", response_model=BatchResponse)
async def create_batch(
    request: BatchCreateRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    repo = BatchRepository(db)
    batch = await repo.create(uuid.UUID(user_id), request.total_photos)
    return batch


@router.delete("/batch/{batch_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_batch(
    batch_id: uuid.UUID,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    batch_repo = BatchRepository(db)
    batch = await batch_repo.get_by_id(batch_id)
    if batch is None or str(batch.user_id) != user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Batch not found")

    if batch.status == "processing":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete a batch that is currently processing",
        )

    photo_repo = PhotoRepository(db)
    photos = await photo_repo.get_by_batch(batch_id)
    for photo in photos:
        for path in [photo.storage_path, photo.thumbnail_path, photo.compressed_path]:
            if path:
                try:
                    delete_file(path)
                except Exception:
                    pass
        await photo_repo.delete(photo.id)

    await batch_repo._db.delete(batch)
    await batch_repo._db.flush()


@router.get("/batch/{batch_id}", response_model=list[PhotoResponse])
async def get_batch_photos(
    batch_id: uuid.UUID,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    batch_repo = BatchRepository(db)
    batch = await batch_repo.get_by_id(batch_id)
    if batch is None or str(batch.user_id) != user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Batch not found")

    photo_repo = PhotoRepository(db)
    photos = await photo_repo.get_by_batch(batch_id)

    result = []
    for photo in photos:
        urls = get_photo_urls(photo)
        photo_data = PhotoResponse.model_validate(photo)
        photo_data.thumbnail_url = urls["thumbnail_url"]
        photo_data.compressed_url = urls["compressed_url"]
        result.append(photo_data)
    return result


# ── Photo ──

@router.post("/upload", response_model=PhotoUploadResponse)
async def upload_photo(
    batch_id: str = Form(...),
    file: UploadFile = File(...),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    try:
        batch_uuid = uuid.UUID(batch_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid batch_id format")

    batch_repo = BatchRepository(db)
    batch = await batch_repo.get_by_id(batch_uuid)
    if batch is None or str(batch.user_id) != user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Batch not found")

    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Empty file")

    photo_id = uuid.uuid4()

    try:
        upload_result = await process_upload(photo_id, file_bytes, file.filename or "photo.jpg")
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Upload processing failed")

    photo_repo = PhotoRepository(db)
    photo = await photo_repo.create(
        id=photo_id,
        batch_id=batch_uuid,
        user_id=uuid.UUID(user_id),
        original_filename=file.filename or "photo.jpg",
        **upload_result,
    )

    await batch_repo.increment_uploaded(batch_uuid)

    urls = get_photo_urls(photo)
    return PhotoUploadResponse(
        id=photo.id,
        batch_id=photo.batch_id,
        original_filename=photo.original_filename,
        thumbnail_url=urls["thumbnail_url"],
    )


@router.get("/{photo_id}", response_model=PhotoDetailResponse)
async def get_photo_detail(
    photo_id: uuid.UUID,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    photo_repo = PhotoRepository(db)
    photo = await photo_repo.get_by_id(photo_id)
    if photo is None or str(photo.user_id) != user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Photo not found")

    urls = get_photo_urls(photo)
    photo_resp = PhotoResponse.model_validate(photo)
    photo_resp.thumbnail_url = urls["thumbnail_url"]
    photo_resp.compressed_url = urls["compressed_url"]

    analysis_resp = None
    if photo.analysis:
        analysis_resp = PhotoAnalysisResponse.model_validate(photo.analysis)

    return PhotoDetailResponse(photo=photo_resp, analysis=analysis_resp)


@router.delete("/{photo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_photo(
    photo_id: uuid.UUID,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    photo_repo = PhotoRepository(db)
    photo = await photo_repo.get_by_id(photo_id)
    if photo is None or str(photo.user_id) != user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Photo not found")

    for path in [photo.storage_path, photo.thumbnail_path, photo.compressed_path]:
        if path:
            try:
                delete_file(path)
            except Exception:
                pass

    await photo_repo.delete(photo_id)


@router.put("/{photo_id}/mark-best", response_model=MarkBestResponse)
async def mark_best_photo(
    photo_id: uuid.UUID,
    request: MarkBestRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    photo_repo = PhotoRepository(db)
    photo = await photo_repo.get_by_id(photo_id)
    if photo is None or str(photo.user_id) != user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Photo not found")

    if not photo.analysis or not photo.analysis.similarity_group:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Photo has no similarity group",
        )

    similarity_group = photo.analysis.similarity_group

    analysis_repo = PhotoAnalysisRepository(db)
    await analysis_repo.unmark_best_in_group(similarity_group, request.task_id)
    analysis = await analysis_repo.mark_best(photo_id)

    selection_repo = UserSelectionRepository(db)
    await selection_repo.upsert(
        user_id=uuid.UUID(user_id),
        photo_id=photo_id,
        similarity_group=similarity_group,
        task_id=request.task_id,
    )

    return MarkBestResponse(
        photo_id=photo_id,
        similarity_group=similarity_group,
        is_best_in_group=analysis.is_best_in_group if analysis else True,
    )
