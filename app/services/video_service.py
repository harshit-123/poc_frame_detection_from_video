import os
import uuid

import cv2

from app.schemas.responses import MatchResult


class VideoService:
    def __init__(
        self,
        face_service,
        matching_service,
        snapshot_dir: str,
        similarity_threshold: float,
    ) -> None:
        self.face_service = face_service
        self.matching_service = matching_service
        self.snapshot_dir = snapshot_dir
        self.similarity_threshold = similarity_threshold

    @staticmethod
    def _person_crop_from_face(frame, face_bbox):
        x1, y1, x2, y2 = face_bbox.astype(int)
        frame_h, frame_w, _ = frame.shape

        face_w = max(1, x2 - x1)
        face_h = max(1, y2 - y1)

        # Heuristic expansion from face box to approximate full-person crop.
        # Wider and much taller area helps capture torso/legs when visible.
        person_x1 = x1 - int(face_w * 1.2)
        person_x2 = x2 + int(face_w * 1.2)
        person_y1 = y1 - int(face_h * 0.8)
        person_y2 = y2 + int(face_h * 5.5)

        person_x1 = max(0, person_x1)
        person_y1 = max(0, person_y1)
        person_x2 = min(frame_w, person_x2)
        person_y2 = min(frame_h, person_y2)

        return frame[person_y1:person_y2, person_x1:person_x2]

    def process_video(self, video_path: str) -> list[MatchResult]:
        cap = cv2.VideoCapture(video_path)

        fps = cap.get(cv2.CAP_PROP_FPS)
        if fps <= 0:
            fps = 1

        frame_number = 0
        matches: list[MatchResult] = []

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            if frame_number % int(fps) != 0:
                frame_number += 1
                continue

            faces = self.face_service.get_faces(frame)

            for face in faces:
                normalized_embedding = self.face_service.normalize_embedding(face.embedding)
                if normalized_embedding is None:
                    continue

                user_id, similarity = self.matching_service.match(normalized_embedding)
                if user_id is None or similarity <= self.similarity_threshold:
                    continue

                crop = self._person_crop_from_face(frame, face.bbox)
                if crop.size == 0:
                    continue

                user_snapshot_dir = os.path.join(self.snapshot_dir, user_id)
                os.makedirs(user_snapshot_dir, exist_ok=True)
                snapshot_path = os.path.join(user_snapshot_dir, f"{uuid.uuid4()}.jpg")
                cv2.imwrite(snapshot_path, crop)

                matches.append(
                    MatchResult(
                        user_id=user_id,
                        timestamp=frame_number / fps,
                        similarity=similarity,
                        snapshot=snapshot_path,
                    )
                )

            frame_number += 1

        cap.release()
        return matches
