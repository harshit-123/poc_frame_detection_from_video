import os
import uuid

import cv2
from fastapi import APIRouter, File, UploadFile

from app.core.config import settings
from app.dependencies import face_service, matching_service, video_service
from app.schemas.responses import (
    ErrorResponse,
    ProcessVideoResponse,
    UploadUserResponse,
)
from app.utils.files import save_upload_file

router = APIRouter()


@router.post("/upload-user", response_model=UploadUserResponse | ErrorResponse)
async def upload_user(file: UploadFile = File(...)):
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

    return UploadUserResponse(message="User registered", user_id=user_id)


@router.post("/process-video", response_model=ProcessVideoResponse | ErrorResponse)
async def process_video(file: UploadFile = File(...)):
    if not matching_service.has_target():
        return ErrorResponse(error="No uploaded user found. Upload a user image first.")

    video_id = str(uuid.uuid4())
    video_path = os.path.join(settings.upload_dir, f"{video_id}.mp4")
    save_upload_file(file, video_path)

    matches = video_service.process_video(video_path)
    return ProcessVideoResponse(matches=matches)
