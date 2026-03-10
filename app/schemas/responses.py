from pydantic import BaseModel


class ErrorResponse(BaseModel):
    error: str


class UploadVideoResponse(BaseModel):
    message: str
    video_id: str


class MatchResult(BaseModel):
    user_id: str
    timestamp: float
    similarity: float
    snapshot: str


class UploadUserResponse(BaseModel):
    message: str
    user_id: str
    matches: list[MatchResult]


class VideoClipResult(BaseModel):
    user_id: str
    timestamp: float
    similarity: float
    clip: str
    duration: float


class UploadUserVideoResponse(BaseModel):
    message: str
    user_id: str
    clips: list[VideoClipResult]
