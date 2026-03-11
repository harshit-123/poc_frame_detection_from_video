import os
import shutil
import subprocess
import uuid
import logging

import cv2

from app.schemas.responses import MatchResult, VideoClipResult

logger = logging.getLogger(__name__)


class VideoService:
    @staticmethod
    def _probe_video_stream(video_path: str) -> dict[str, str] | None:
        ffprobe_path = shutil.which("ffprobe")
        if ffprobe_path is None or not os.path.exists(video_path):
            return None

        command = [
            ffprobe_path,
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_entries",
            "stream=codec_name,pix_fmt",
            "-of",
            "default=noprint_wrappers=1",
            video_path,
        ]
        result = subprocess.run(command, capture_output=True, check=False)
        if result.returncode != 0:
            logger.warning(
                "ffprobe failed for %s: %s",
                video_path,
                result.stderr.decode("utf-8", errors="ignore").strip(),
            )
            return None

        stream_info: dict[str, str] = {}
        for line in result.stdout.decode("utf-8", errors="ignore").splitlines():
            if "=" not in line:
                continue
            key, value = line.split("=", 1)
            stream_info[key.strip()] = value.strip()
        return stream_info or None

    @classmethod
    def _is_browser_compatible_mp4(cls, video_path: str) -> bool:
        stream_info = cls._probe_video_stream(video_path)
        if stream_info is None:
            return False
        return (
            stream_info.get("codec_name") == "h264"
            and stream_info.get("pix_fmt") == "yuv420p"
        )

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
    def _transcode_clip_for_web(source_path: str) -> str:
        ffmpeg_path = shutil.which("ffmpeg")
        if ffmpeg_path is None:
            return source_path

        base, ext = os.path.splitext(source_path)
        if ext.lower() != ".mp4":
            return source_path
        output_path = f"{base}_fixed.mp4"

        command = [
            ffmpeg_path,
            "-y",
            "-i",
            source_path,
            "-c:v",
            "libx264",
            "-preset",
            "fast",
            "-crf",
            "23",
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",
            output_path,
        ]
        result = subprocess.run(command, capture_output=True, check=False)
        if result.returncode != 0 or not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
            logger.warning(
                "ffmpeg transcode failed for %s: %s",
                source_path,
                result.stderr.decode("utf-8", errors="ignore").strip(),
            )
            return source_path
        if not VideoService._is_browser_compatible_mp4(output_path):
            logger.warning("Transcoded clip is not browser compatible: %s", output_path)
            return source_path
        return output_path

    @staticmethod
    def _write_video_clip_with_ffmpeg(
        video_path: str,
        clip_path: str,
        start_sec: float,
        duration_sec: float,
    ) -> str | None:
        ffmpeg_path = shutil.which("ffmpeg")
        if ffmpeg_path is None:
            return None

        command = [
            ffmpeg_path,
            "-y",
            "-i",
            video_path,
            "-ss",
            f"{start_sec:.3f}",
            "-t",
            f"{duration_sec:.3f}",
            "-c:v",
            "libx264",
            "-preset",
            "fast",
            "-crf",
            "23",
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",
            "-an",
            clip_path,
        ]
        result = subprocess.run(command, capture_output=True, check=False)
        if result.returncode != 0 or not os.path.exists(clip_path) or os.path.getsize(clip_path) == 0:
            logger.warning(
                "ffmpeg clip extraction failed for %s [%ss-%ss]: %s",
                video_path,
                f"{start_sec:.3f}",
                f"{start_sec + duration_sec:.3f}",
                result.stderr.decode("utf-8", errors="ignore").strip(),
            )
            if os.path.exists(clip_path):
                os.remove(clip_path)
            return None
        if not VideoService._is_browser_compatible_mp4(clip_path):
            logger.warning("ffmpeg generated clip is not browser compatible: %s", clip_path)
            if os.path.exists(clip_path):
                os.remove(clip_path)
            return None
        return clip_path

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

    def extract_target_embedding(self, video_path: str):
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        if fps <= 0:
            fps = 1

        frame_number = 0
        sample_interval = max(1, int(fps))
        embedding = None

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            if frame_number % sample_interval != 0:
                frame_number += 1
                continue

            faces = self.face_service.get_faces(frame)
            if len(faces) == 0:
                frame_number += 1
                continue

            normalized_embedding = self.face_service.normalize_embedding(faces[0].embedding)
            if normalized_embedding is not None:
                embedding = normalized_embedding
                break

            frame_number += 1

        cap.release()
        return embedding

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

    def _write_video_clip(
        self,
        video_path: str,
        user_id: str,
        start_sec: float,
        end_sec: float,
    ) -> str | None:
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        if fps <= 0:
            fps = 1

        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        start_frame = max(0, int(start_sec * fps))
        end_frame = int(end_sec * fps)
        if total_frames > 0:
            end_frame = min(total_frames - 1, end_frame)

        if end_frame <= start_frame or frame_width <= 0 or frame_height <= 0:
            cap.release()
            return None

        user_clip_dir = os.path.join(self.snapshot_dir, user_id, "clips")
        os.makedirs(user_clip_dir, exist_ok=True)
        clip_path = os.path.join(user_clip_dir, f"{uuid.uuid4()}.mp4")

        duration_sec = max(0.1, end_sec - start_sec)
        ffmpeg_clip_path = self._write_video_clip_with_ffmpeg(
            video_path=video_path,
            clip_path=clip_path,
            start_sec=start_sec,
            duration_sec=duration_sec,
        )
        if ffmpeg_clip_path is not None:
            cap.release()
            return ffmpeg_clip_path

        cap.release()
        logger.warning("Skipping clip because ffmpeg could not generate a browser-compatible MP4")
        return None

    def process_video_clips(
        self,
        video_path: str,
        clip_duration_sec: float = 4.0,
        max_clips: int = 5,
    ) -> list[VideoClipResult]:
        cap = cv2.VideoCapture(video_path)

        fps = cap.get(cv2.CAP_PROP_FPS)
        if fps <= 0:
            fps = 1

        frame_number = 0
        clips: list[VideoClipResult] = []
        last_clip_time_by_user: dict[str, float] = {}

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            if frame_number % int(fps) != 0:
                frame_number += 1
                continue

            faces = self.face_service.get_faces(frame)
            timestamp = frame_number / fps

            for face in faces:
                normalized_embedding = self.face_service.normalize_embedding(face.embedding)
                if normalized_embedding is None:
                    continue

                user_id, similarity = self.matching_service.match(normalized_embedding)
                if user_id is None or similarity <= self.similarity_threshold:
                    continue

                # Skip very close timestamps to avoid creating many overlapping clips.
                last_clip_time = last_clip_time_by_user.get(user_id)
                if last_clip_time is not None and (timestamp - last_clip_time) < 2.0:
                    continue

                half_duration = clip_duration_sec / 2
                start_sec = max(0.0, timestamp - half_duration)
                end_sec = timestamp + half_duration
                clip_path = self._write_video_clip(
                    video_path=video_path,
                    user_id=user_id,
                    start_sec=start_sec,
                    end_sec=end_sec,
                )
                if clip_path is None:
                    continue

                last_clip_time_by_user[user_id] = timestamp
                clips.append(
                    VideoClipResult(
                        user_id=user_id,
                        timestamp=timestamp,
                        similarity=similarity,
                        clip=clip_path,
                        duration=clip_duration_sec,
                    )
                )
                if len(clips) >= max_clips:
                    cap.release()
                    return clips

            frame_number += 1

        cap.release()
        return clips
