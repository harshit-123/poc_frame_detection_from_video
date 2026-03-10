import os
from typing import Any
from urllib.parse import quote

import requests
import streamlit as st


DEFAULT_API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")
MAX_VIDEO_UPLOAD_SIZE_BYTES = 300 * 1024 * 1024
API_REQUEST_TIMEOUT_SECONDS = 900


def post_file(
    api_base_url: str,
    endpoint: str,
    file_field: str,
    uploaded_file,
    extra_data: dict[str, Any] | None = None,
) -> tuple[bool, dict[str, Any]]:
    url = f"{api_base_url.rstrip('/')}{endpoint}"
    files = {file_field: (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
    data = extra_data or {}

    try:
        response = requests.post(
            url,
            files=files,
            data=data,
            timeout=(10, API_REQUEST_TIMEOUT_SECONDS),
        )
    except requests.RequestException as exc:
        return False, {"error": f"Request failed: {exc}"}

    try:
        payload = response.json()
    except ValueError:
        return False, {"error": f"Invalid API response (status {response.status_code})"}

    if response.status_code >= 400:
        return False, payload
    return True, payload


def render_admin_page(api_base_url: str) -> None:
    st.header("Admin Video Upload")
    st.write("Upload source video first. Users can then upload photos to get matched clips.")

    admin_video = st.file_uploader(
        "Choose a video file",
        type=["mp4", "mov", "avi", "mkv"],
        key="admin_video_uploader",
    )

    if st.button("Upload Admin Video", use_container_width=True):
        if admin_video is None:
            st.error("Please select a video file.")
            return
        if admin_video.size > MAX_VIDEO_UPLOAD_SIZE_BYTES:
            st.error("Video size exceeds 300 MB limit.")
            return

        ok, payload = post_file(
            api_base_url=api_base_url,
            endpoint="/admin-video-upload",
            file_field="file",
            uploaded_file=admin_video,
        )
        if not ok:
            st.error(payload.get("error", "Failed to upload admin video."))
            return

        st.success(payload.get("message", "Admin video uploaded successfully."))
        st.json(payload)


def render_user_page(api_base_url: str) -> None:
    st.header("User Photo Upload")
    st.write("Upload your photo to generate 3-5 second matched video clips.")

    user_photo = st.file_uploader(
        "Choose a photo",
        type=["jpg", "jpeg", "png"],
        key="user_photo_uploader",
    )
    clip_duration = st.slider(
        "Clip Duration (seconds)",
        min_value=3.0,
        max_value=5.0,
        value=4.0,
        step=0.5,
    )
    max_clips = st.slider(
        "Maximum Clips",
        min_value=1,
        max_value=20,
        value=5,
        step=1,
    )

    if st.button("Upload Photo and Generate Clips", use_container_width=True):
        if user_photo is None:
            st.error("Please select a photo file.")
            return

        with st.spinner("Generating clips, please wait..."):
            ok, payload = post_file(
                api_base_url=api_base_url,
                endpoint="/user-photo-upload-video-clip",
                file_field="file",
                uploaded_file=user_photo,
                extra_data={
                    "clip_duration_sec": str(clip_duration),
                    "max_clips": str(max_clips),
                },
            )
        if not ok:
            st.error(payload.get("error", "Failed to generate clips."))
            return

        st.success(payload.get("message", "Clips generated."))
        st.write(f"User ID: `{payload.get('user_id', '-')}`")
        clips = payload.get("clips", [])
        if not clips:
            st.warning("No clips were generated for this user.")
            st.json(payload)
            return

        st.subheader("Generated Clips")
        for index, clip in enumerate(clips, start=1):
            clip_path = clip.get("clip", "")
            st.write(
                f"{index}. timestamp={clip.get('timestamp')}s, "
                f"similarity={clip.get('similarity')}, duration={clip.get('duration')}s"
            )
            if clip_path:
                clip_url = f"{api_base_url.rstrip('/')}/clip-file?path={quote(clip_path)}"
                st.video(clip_url, format="video/mp4")
                st.caption(f"Clip path: `{clip_path}`")
            else:
                st.info(f"Clip saved on API server: `{clip_path}`")


def main() -> None:
    st.set_page_config(page_title="Video Match UI", layout="wide")
    st.title("POC Video Match")

    api_base_url = st.sidebar.text_input("API Base URL", value=DEFAULT_API_BASE_URL)
    page = st.sidebar.radio("Page", options=["Admin", "User"], index=0)

    if page == "Admin":
        render_admin_page(api_base_url)
    else:
        render_user_page(api_base_url)


if __name__ == "__main__":
    main()
