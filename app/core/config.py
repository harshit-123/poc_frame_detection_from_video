import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    upload_dir: str = os.getenv("UPLOAD_DIR", "uploads")
    snapshot_dir: str = os.getenv("SNAPSHOT_DIR", "snapshots")
    face_model_name: str = os.getenv("FACE_MODEL_NAME", "buffalo_l")
    face_ctx_id: int = int(os.getenv("FACE_CTX_ID", "0"))
    embedding_dimension: int = int(os.getenv("EMBEDDING_DIMENSION", "512"))
    similarity_threshold: float = float(os.getenv("SIMILARITY_THRESHOLD", "0.6"))


settings = Settings()
