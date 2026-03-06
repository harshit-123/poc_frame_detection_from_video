# poc_video_frame

Modular FastAPI service for:
- registering one target user face from an uploaded image
- scanning uploaded video frames for that user
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

## Endpoints

- `POST /upload-user` with image file form field `file`
- `POST /process-video` with video file form field `file`

Snapshots are written to:
- `snapshots/<user_id>/<uuid>.jpg`
