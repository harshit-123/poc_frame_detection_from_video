import faiss
import numpy as np


class MatchingService:
    def __init__(self, dimension: int) -> None:
        self._index = faiss.IndexFlatIP(dimension)
        self._user_ids: list[str] = []

    def register_target(self, user_id: str, normalized_embedding: np.ndarray) -> None:
        self._index.reset()
        self._user_ids.clear()
        self._index.add(np.array([normalized_embedding], dtype="float32"))
        self._user_ids.append(user_id)

    def has_target(self) -> bool:
        return self._index.ntotal > 0 and len(self._user_ids) > 0

    def match(self, normalized_embedding: np.ndarray) -> tuple[str | None, float]:
        if not self.has_target():
            return None, 0.0

        distances, indices = self._index.search(
            np.array([normalized_embedding], dtype="float32"),
            1,
        )

        similarity = float(distances[0][0])
        index = int(indices[0][0])
        if index < 0 or index >= len(self._user_ids):
            return None, similarity

        return self._user_ids[index], similarity
