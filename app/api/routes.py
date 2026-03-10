import os
import uuid

import cv2
from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse

from app.core.config import settings
from app.dependencies import face_service, matching_service, video_service
from app.schemas.responses import (
    ErrorResponse,
    UploadUserResponse,
    UploadUserVideoResponse,
    UploadVideoResponse,
)
from app.utils.files import save_upload_file

router = APIRouter()

# In-memory reference to the most recent admin video for matching.
_latest_admin_video_path: str | None = None
MAX_VIDEO_UPLOAD_SIZE_BYTES = 300 * 1024 * 1024


def _uploaded_file_size(upload_file: UploadFile) -> int:
    upload_file.file.seek(0, os.SEEK_END)
    size = upload_file.file.tell()
    upload_file.file.seek(0)
    return size


@router.get("/clip-file")
async def get_clip_file(path: str = Query(...)):
    snapshot_dir_abs = os.path.abspath(settings.snapshot_dir)
    clip_path_abs = os.path.abspath(path)
    if not clip_path_abs.startswith(snapshot_dir_abs + os.sep):
        raise HTTPException(status_code=400, detail="Invalid clip path")
    if not os.path.exists(clip_path_abs):
        raise HTTPException(status_code=404, detail="Clip not found")
    return FileResponse(clip_path_abs, media_type="video/mp4")


@router.post("/admin-video-upload", response_model=UploadVideoResponse | ErrorResponse)
@router.post("/process-video", response_model=UploadVideoResponse | ErrorResponse)
async def admin_video_upload(file: UploadFile = File(...)):
    global _latest_admin_video_path

    if _uploaded_file_size(file) > MAX_VIDEO_UPLOAD_SIZE_BYTES:
        return ErrorResponse(error="Video size exceeds 300 MB limit.")

    video_id = str(uuid.uuid4())
    video_path = os.path.join(settings.upload_dir, f"admin_{video_id}.mp4")
    save_upload_file(file, video_path)

    _latest_admin_video_path = video_path

    return UploadVideoResponse(
        message="Admin video uploaded successfully",
        video_id=video_id,
    )


@router.post("/user-photo-upload", response_model=UploadUserResponse | ErrorResponse)
async def user_photo_upload(file: UploadFile = File(...)):
    if _latest_admin_video_path is None:
        return ErrorResponse(error="No admin video found. Upload an admin video first.")

    user_id = str(uuid.uuid4())
    image_path = os.path.join(settings.upload_dir, f"{user_id}.jpg")
    save_upload_file(file, image_path)

    image = cv2.imread(image_path)
    embedding = face_service.get_primary_embedding(image)
    if embedding is None:
        return ErrorResponse(error="No face detected")

    normalized_embedding = face_service.normalize_embedding(embedding)
    if normalized_embedding is None:
        return ErrorResponse(error="Invalid face embedding")

    matching_service.register_target(user_id, normalized_embedding)

    matches = video_service.process_video(_latest_admin_video_path)

    return UploadUserResponse(
        message="User registered and snapshots generated",
        user_id=user_id,
        matches=matches,
    )


@router.post(
    "/user-photo-upload-video-clip",
    response_model=UploadUserVideoResponse | ErrorResponse,
)
async def user_photo_upload_video_clip(
    file: UploadFile = File(...),
    clip_duration_sec: float = Form(4.0),
    max_clips: int = Form(5),
):
    if _latest_admin_video_path is None:
        return ErrorResponse(error="No admin video found. Upload an admin video first.")

    user_id = str(uuid.uuid4())
    image_path = os.path.join(settings.upload_dir, f"{user_id}.jpg")
    save_upload_file(file, image_path)

    image = cv2.imread(image_path)
    embedding = face_service.get_primary_embedding(image)
    if embedding is None:
        return ErrorResponse(error="No face detected")

    normalized_embedding = face_service.normalize_embedding(embedding)
    if normalized_embedding is None:
        return ErrorResponse(error="Invalid face embedding")

    matching_service.register_target(user_id, normalized_embedding)

    safe_clip_duration = max(3.0, min(5.0, clip_duration_sec))
    safe_max_clips = max(1, min(20, max_clips))
    clips = video_service.process_video_clips(
        _latest_admin_video_path,
        clip_duration_sec=safe_clip_duration,
        max_clips=safe_max_clips,
    )

    return UploadUserVideoResponse(
        message="User registered and video clips generated",
        user_id=user_id,
        clips=clips,
    )
