# poc_video_frame

Modular FastAPI service for:
- uploading one admin video to be used as the source footage
- registering one target user face from an uploaded image
- scanning admin video frames for that user
- saving matched face snapshots in per-user folders under `snapshots/<user_id>/`

## Project Structure

```text
app/
  api/
    routes.py
  core/
    config.py
  schemas/
    responses.py
  services/
    face_service.py
    matching_service.py
    video_service.py
  utils/
    files.py
  dependencies.py
  main.py
main.py
```

## Run

```bash
uvicorn app.main:app --reload
```

In another terminal, run Streamlit UI:

```bash
streamlit run streamlit_app.py
```

## Endpoints

1. `POST /admin-video-upload` (or legacy `POST /process-video`) with video file form field `file`
2. `POST /user-photo-upload` with image file form field `file`
3. `POST /user-photo-upload-video-clip` with:
   - image file form field `file`
   - optional form field `clip_duration_sec` (clamped between 3 and 5 seconds, default `4.0`)
   - optional form field `max_clips` (clamped between 1 and 20, default `5`)
4. `GET /clip-file?path=<clip_path>` to stream generated clip files

Flow:
- Admin uploads video first.
- User uploads photo after that.
- API can generate either:
  - image snapshots with `/user-photo-upload`
  - short video clips with `/user-photo-upload-video-clip`
- Admin video upload max size: `300 MB`

## Streamlit UI

`streamlit_app.py` provides:
- `Admin` page:
  - upload admin video via `/admin-video-upload`
- `User` page:
  - upload user photo and choose clip duration (3-5 sec)
  - choose maximum clips to generate
  - generate clips via `/user-photo-upload-video-clip`

The Streamlit app fetches generated clips through the API on the server side before rendering them in the browser. This avoids the common EC2 deployment issue where the browser cannot reach `127.0.0.1:8000` even though Streamlit can.
Streamlit upload limit is configured to 300 MB in `.streamlit/config.toml`.

Snapshots are written to:
- `snapshots/<user_id>/<uuid>.jpg`

## EC2 Video Playback Troubleshooting

If clips generate but Chrome shows a blank player on EC2, check these first:

1. Confirm Streamlit can reach the API from the same host.
   - If both run on the same EC2 instance, `API_BASE_URL=http://127.0.0.1:8000` is valid.
   - If they run in different containers/hosts, do not use `127.0.0.1`; use the FastAPI service hostname or private IP.
2. Confirm generated clips are H.264 + `yuv420p`, which browsers expect for MP4 playback.
   - `ffprobe -v error -select_streams v:0 -show_entries stream=codec_name,pix_fmt -of default=noprint_wrappers=1 /path/to/clip.mp4`
   - Expected output is `codec_name=h264` and `pix_fmt=yuv420p`.
3. Confirm EC2 `ffmpeg` has H.264 encoding support.
   - `ffmpeg -encoders | grep libx264`
   - If nothing is returned, install an ffmpeg build that includes `libx264`.

The backend now skips clips that are not browser-compatible instead of returning a broken MP4 file.
