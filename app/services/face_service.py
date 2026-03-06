import numpy as np
from insightface.app import FaceAnalysis


class FaceService:
    def __init__(self, model_name: str, ctx_id: int) -> None:
        self._face_app = FaceAnalysis(name=model_name)
        self._face_app.prepare(ctx_id=ctx_id)

    def get_faces(self, image):
        return self._face_app.get(image)

    def get_primary_embedding(self, image):
        faces = self.get_faces(image)
        if len(faces) == 0:
            return None
        return faces[0].embedding

    @staticmethod
    def normalize_embedding(embedding):
        norm = np.linalg.norm(embedding)
        if norm == 0:
            return None
        return (embedding / norm).astype("float32")
