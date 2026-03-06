from app.core.config import settings
from app.services.face_service import FaceService
from app.services.matching_service import MatchingService
from app.services.video_service import VideoService
from app.utils.files import ensure_directories

ensure_directories(settings.upload_dir, settings.snapshot_dir)

face_service = FaceService(
    model_name=settings.face_model_name,
    ctx_id=settings.face_ctx_id,
)
matching_service = MatchingService(dimension=settings.embedding_dimension)
video_service = VideoService(
    face_service=face_service,
    matching_service=matching_service,
    snapshot_dir=settings.snapshot_dir,
    similarity_threshold=settings.similarity_threshold,
)
