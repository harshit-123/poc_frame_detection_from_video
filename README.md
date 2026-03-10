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

If API and Streamlit run on different machines, the returned clip file paths may not be directly playable in the browser. In that case, use shared storage or add a file-serving endpoint.
Streamlit upload limit is configured to 300 MB in `.streamlit/config.toml`.

Snapshots are written to:
- `snapshots/<user_id>/<uuid>.jpg`
