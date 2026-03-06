from pydantic import BaseModel


class ErrorResponse(BaseModel):
    error: str


class UploadUserResponse(BaseModel):
    message: str
    user_id: str


class MatchResult(BaseModel):
    user_id: str
    timestamp: float
    similarity: float
    snapshot: str


class ProcessVideoResponse(BaseModel):
    matches: list[MatchResult]
