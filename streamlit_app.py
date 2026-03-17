"""
Face Match Video Generator — Production UI
"""

import os
from typing import Any
from urllib.parse import quote

import requests
import streamlit as st

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
DEFAULT_API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")
MAX_VIDEO_UPLOAD_SIZE_BYTES = 300 * 1024 * 1024
API_REQUEST_TIMEOUT_SECONDS = 900
ALLOWED_ADMIN_VIDEO_CONTENT_TYPES = {
    "video/mp4",
    "video/quicktime",
    "video/x-msvideo",
    "video/x-matroska",
    "video/mpeg",
}
ALLOWED_ADMIN_VIDEO_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv", ".mpeg", ".mpg"}
ALLOWED_USER_IMAGE_CONTENT_TYPES = {"image/png", "image/jpeg"}
ALLOWED_USER_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg"}


# ---------------------------------------------------------------------------
# Custom CSS
# ---------------------------------------------------------------------------
def inject_custom_css() -> None:
    st.markdown(
        """
        <style>
        /* ---------- Google Font ---------- */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

        /* ---------- Root variables ---------- */
        :root {
            --bg-primary: #0f0f1a;
            --bg-secondary: #161625;
            --bg-card: rgba(25, 25, 50, 0.65);
            --bg-card-hover: rgba(35, 35, 70, 0.75);
            --border-card: rgba(120, 100, 255, 0.15);
            --border-card-hover: rgba(120, 100, 255, 0.35);
            --accent-primary: #7c5cfc;
            --accent-secondary: #00d4ff;
            --accent-gradient: linear-gradient(135deg, #7c5cfc, #00d4ff);
            --accent-gradient-hover: linear-gradient(135deg, #9478ff, #33ddff);
            --text-primary: #e8e6f0;
            --text-secondary: #9993b8;
            --text-muted: #6b6490;
            --success: #22c55e;
            --warning: #f59e0b;
            --error: #ef4444;
            --radius: 16px;
            --radius-sm: 10px;
            --shadow-card: 0 8px 32px rgba(0, 0, 0, 0.35);
            --shadow-glow: 0 0 30px rgba(124, 92, 252, 0.12);
        }

        /* ---------- Global ---------- */
        html, body, [data-testid="stAppViewContainer"], [data-testid="stApp"] {
            font-family: 'Inter', sans-serif !important;
            color: var(--text-primary) !important;
        }

        [data-testid="stAppViewContainer"] {
            background: var(--bg-primary) !important;
            background-image:
                radial-gradient(ellipse 80% 60% at 50% 0%, rgba(124,92,252,0.08), transparent),
                radial-gradient(ellipse 60% 50% at 80% 100%, rgba(0,212,255,0.06), transparent) !important;
        }

        /* ---------- Sidebar ---------- */
        [data-testid="stSidebar"] {
            background: var(--bg-secondary) !important;
            border-right: 1px solid var(--border-card) !important;
        }
        [data-testid="stSidebar"] .stMarkdown p,
        [data-testid="stSidebar"] .stMarkdown span,
        [data-testid="stSidebar"] label {
            color: var(--text-secondary) !important;
        }
        [data-testid="stSidebar"] .stRadio > label {
            color: var(--text-secondary) !important;
            font-weight: 500 !important;
        }

        /* ---------- Headers ---------- */
        h1 {
            background: var(--accent-gradient);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            font-weight: 800 !important;
            letter-spacing: -0.5px;
        }
        h2, h3 {
            color: var(--text-primary) !important;
            font-weight: 700 !important;
        }

        /* ---------- Card container ---------- */
        .glass-card {
            background: var(--bg-card);
            border: 1px solid var(--border-card);
            border-radius: var(--radius);
            padding: 28px 32px;
            margin: 12px 0;
            backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
            box-shadow: var(--shadow-card);
            transition: all 0.35s cubic-bezier(0.4, 0, 0.2, 1);
        }
        .glass-card:hover {
            border-color: var(--border-card-hover);
            box-shadow: var(--shadow-card), var(--shadow-glow);
            transform: translateY(-2px);
        }

        /* ---------- Upload zone ---------- */
        .upload-zone {
            border: 2px dashed rgba(124, 92, 252, 0.3);
            border-radius: var(--radius);
            padding: 48px 32px;
            text-align: center;
            transition: all 0.3s ease;
            background: rgba(124, 92, 252, 0.03);
            margin: 16px 0;
        }
        .upload-zone:hover {
            border-color: var(--accent-primary);
            background: rgba(124, 92, 252, 0.08);
        }
        .upload-icon {
            font-size: 48px;
            margin-bottom: 12px;
            animation: float 3s ease-in-out infinite;
        }

        /* ---------- Buttons ---------- */
        .stButton > button {
            background: var(--accent-gradient) !important;
            color: white !important;
            border: none !important;
            border-radius: var(--radius-sm) !important;
            padding: 12px 32px !important;
            font-weight: 600 !important;
            font-size: 15px !important;
            letter-spacing: 0.3px;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
            box-shadow: 0 4px 15px rgba(124, 92, 252, 0.3) !important;
        }
        .stButton > button:hover {
            background: var(--accent-gradient-hover) !important;
            transform: translateY(-2px) !important;
            box-shadow: 0 8px 25px rgba(124, 92, 252, 0.45) !important;
        }
        .stButton > button:active {
            transform: translateY(0) !important;
        }

        /* ---------- Slider ---------- */
        .stSlider [data-baseweb="slider"] [role="slider"] {
            background: var(--accent-primary) !important;
            border-color: var(--accent-primary) !important;
        }
        .stSlider [data-baseweb="slider"] div[data-testid="stTickBar"] {
            background: rgba(124, 92, 252, 0.3) !important;
        }

        /* ---------- File uploader ---------- */
        [data-testid="stFileUploader"] {
            border-radius: var(--radius-sm) !important;
        }
        [data-testid="stFileUploader"] section {
            border: 1px dashed var(--border-card) !important;
            border-radius: var(--radius-sm) !important;
            padding: 20px !important;
            transition: border-color 0.3s ease !important;
        }
        [data-testid="stFileUploader"] section:hover {
            border-color: var(--accent-primary) !important;
        }

        /* ---------- Metric cards ---------- */
        .metric-card {
            background: var(--bg-card);
            border: 1px solid var(--border-card);
            border-radius: var(--radius-sm);
            padding: 16px 20px;
            text-align: center;
        }
        .metric-value {
            font-size: 28px;
            font-weight: 700;
            background: var(--accent-gradient);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        .metric-label {
            font-size: 12px;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-top: 4px;
        }

        /* ---------- Clip card ---------- */
        .clip-card {
            background: var(--bg-card);
            border: 1px solid var(--border-card);
            border-radius: var(--radius);
            overflow: hidden;
            transition: all 0.35s cubic-bezier(0.4, 0, 0.2, 1);
            animation: fadeSlideUp 0.5s ease-out both;
        }
        .clip-card:hover {
            border-color: var(--border-card-hover);
            transform: translateY(-4px);
            box-shadow: var(--shadow-card), var(--shadow-glow);
        }
        .clip-meta {
            padding: 16px;
        }
        .clip-badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 11px;
            font-weight: 600;
            letter-spacing: 0.5px;
        }
        .badge-timestamp {
            background: rgba(124, 92, 252, 0.15);
            color: #a78bfa;
        }
        .badge-similarity {
            background: rgba(34, 197, 94, 0.15);
            color: #4ade80;
        }
        .badge-duration {
            background: rgba(0, 212, 255, 0.15);
            color: #67e8f9;
        }

        /* ---------- Similarity bar ---------- */
        .sim-bar-track {
            width: 100%;
            height: 6px;
            background: rgba(255,255,255,0.06);
            border-radius: 3px;
            margin-top: 10px;
            overflow: hidden;
        }
        .sim-bar-fill {
            height: 100%;
            border-radius: 3px;
            background: var(--accent-gradient);
            transition: width 0.8s cubic-bezier(0.4, 0, 0.2, 1);
        }

        /* ---------- Status indicator ---------- */
        .status-dot {
            display: inline-block;
            width: 10px;
            height: 10px;
            border-radius: 50%;
            margin-right: 8px;
        }
        .status-active {
            background: var(--success);
            box-shadow: 0 0 8px rgba(34, 197, 94, 0.5);
            animation: pulse 2s infinite;
        }
        .status-inactive {
            background: var(--text-muted);
        }

        /* ---------- Success banner ---------- */
        .success-banner {
            background: linear-gradient(135deg, rgba(34,197,94,0.1), rgba(0,212,255,0.05));
            border: 1px solid rgba(34,197,94,0.25);
            border-radius: var(--radius-sm);
            padding: 20px 24px;
            animation: slideIn 0.4s ease-out;
        }
        .success-banner h4 {
            color: var(--success) !important;
            margin: 0 0 6px 0;
        }

        /* ---------- Info card ---------- */
        .info-card {
            background: rgba(0, 212, 255, 0.04);
            border: 1px solid rgba(0, 212, 255, 0.15);
            border-radius: var(--radius-sm);
            padding: 16px 20px;
            color: var(--text-secondary);
            font-size: 14px;
        }

        /* ---------- Empty state ---------- */
        .empty-state {
            text-align: center;
            padding: 60px 32px;
            color: var(--text-muted);
        }
        .empty-state-icon {
            font-size: 56px;
            margin-bottom: 16px;
            opacity: 0.6;
        }

        /* ---------- Section divider ---------- */
        .section-divider {
            height: 1px;
            background: linear-gradient(90deg, transparent, var(--border-card), transparent);
            margin: 24px 0;
        }

        /* ---------- Step flow ---------- */
        .step-flow {
            display: flex;
            gap: 8px;
            align-items: center;
            justify-content: center;
            margin: 20px 0;
            flex-wrap: wrap;
        }
        .step-item {
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 8px 16px;
            border-radius: 8px;
            font-size: 13px;
            font-weight: 500;
        }
        .step-active {
            background: rgba(124, 92, 252, 0.1);
            color: var(--accent-primary);
            border: 1px solid rgba(124, 92, 252, 0.2);
        }
        .step-inactive {
            color: var(--text-muted);
            border: 1px solid rgba(255,255,255,0.05);
        }
        .step-arrow {
            color: var(--text-muted);
            font-size: 14px;
        }

        /* ---------- Animations ---------- */
        @keyframes fadeSlideUp {
            from {
                opacity: 0;
                transform: translateY(20px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        @keyframes slideIn {
            from {
                opacity: 0;
                transform: translateX(-20px);
            }
            to {
                opacity: 1;
                transform: translateX(0);
            }
        }

        @keyframes float {
            0%, 100% { transform: translateY(0px); }
            50% { transform: translateY(-8px); }
        }

        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }

        @keyframes gradientShift {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }

        .page-enter {
            animation: fadeSlideUp 0.6s ease-out;
        }

        /* ---------- Celebration ---------- */
        .celebration {
            position: relative;
        }
        .celebration::after {
            content: '🎉';
            position: absolute;
            top: -10px;
            right: -10px;
            font-size: 24px;
            animation: float 2s ease-in-out infinite;
        }

        /* ---------- Stagger clip card animations ---------- */
        .clip-card:nth-child(1) { animation-delay: 0s; }
        .clip-card:nth-child(2) { animation-delay: 0.1s; }
        .clip-card:nth-child(3) { animation-delay: 0.2s; }
        .clip-card:nth-child(4) { animation-delay: 0.3s; }
        .clip-card:nth-child(5) { animation-delay: 0.4s; }
        .clip-card:nth-child(6) { animation-delay: 0.5s; }

        /* ---------- Responsive ---------- */
        @media (max-width: 768px) {
            .glass-card { padding: 20px; }
            .upload-zone { padding: 32px 20px; }
        }

        /* ---------- Override Streamlit alerts ---------- */
        .stAlert { border-radius: var(--radius-sm) !important; }

        /* ---------- Expander ---------- */
        .streamlit-expanderHeader {
            font-weight: 600 !important;
            color: var(--text-secondary) !important;
        }

        /* ---------- Text input ---------- */
        .stTextInput > div > div > input {
            background: var(--bg-card) !important;
            border: 1px solid var(--border-card) !important;
            border-radius: var(--radius-sm) !important;
            color: var(--text-primary) !important;
        }
        .stTextInput > div > div > input:focus {
            border-color: var(--accent-primary) !important;
            box-shadow: 0 0 0 2px rgba(124, 92, 252, 0.2) !important;
        }

        /* ---------- Spinner ---------- */
        .stSpinner > div {
            border-color: var(--accent-primary) !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _file_extension(uploaded_file) -> str:
    return os.path.splitext(uploaded_file.name or "")[1].lower()


def _is_allowed_file(
    uploaded_file,
    *,
    allowed_content_types: set[str],
    allowed_extensions: set[str],
) -> bool:
    content_type = (uploaded_file.type or "").lower()
    extension = _file_extension(uploaded_file)
    return content_type in allowed_content_types or extension in allowed_extensions


def _human_size(size_bytes: int) -> str:
    if size_bytes < 1024:
        return f"{size_bytes} B"
    if size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    return f"{size_bytes / (1024 * 1024):.1f} MB"


# ---------------------------------------------------------------------------
# API helpers
# ---------------------------------------------------------------------------
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


def fetch_binary(url: str) -> tuple[bool, bytes | None, str | None]:
    try:
        response = requests.get(url, timeout=(10, API_REQUEST_TIMEOUT_SECONDS))
    except requests.RequestException as exc:
        return False, None, f"Request failed: {exc}"
    if response.status_code >= 400:
        error_message = f"Failed to fetch media (status {response.status_code})"
        try:
            payload = response.json()
        except ValueError:
            payload = None
        if isinstance(payload, dict) and payload.get("detail"):
            error_message = f"{error_message}: {payload['detail']}"
        return False, None, error_message
    content_type = response.headers.get("content-type", "")
    if "video/mp4" not in content_type.lower():
        return False, None, f"Unexpected media type: {content_type or 'missing content-type'}"
    if not response.content:
        return False, None, "Media response was empty"
    return True, response.content, None


# ---------------------------------------------------------------------------
# UI Components
# ---------------------------------------------------------------------------
def render_step_flow(active_step: int = 1) -> None:
    steps = [
        ("📁", "Upload"),
        ("⚙️", "Process"),
        ("🎬", "Results"),
    ]
    items = []
    for i, (icon, label) in enumerate(steps):
        css_class = "step-active" if i + 1 == active_step else "step-inactive"
        items.append(f'<div class="step-item {css_class}">{icon} {label}</div>')
        if i < len(steps) - 1:
            items.append('<span class="step-arrow">→</span>')
    st.markdown(
        f'<div class="step-flow">{"".join(items)}</div>',
        unsafe_allow_html=True,
    )


def render_file_info(uploaded_file) -> None:
    size = _human_size(uploaded_file.size)
    ext = _file_extension(uploaded_file)
    st.markdown(
        f"""
        <div class="info-card" style="margin-top:12px;">
            <strong>📄 {uploaded_file.name}</strong><br>
            <span style="color:var(--text-muted); font-size:13px;">
                Size: {size} &nbsp;•&nbsp; Type: {ext.upper().lstrip('.')}
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_clip_card(
    index: int,
    clip: dict[str, Any],
    clip_bytes: bytes | None,
    error_message: str | None,
) -> None:
    timestamp = clip.get("timestamp", 0)
    similarity = clip.get("similarity", 0)
    duration = clip.get("duration", 0)
    sim_pct = round(similarity * 100, 1)

    st.markdown(
        f"""
        <div class="clip-card" style="animation-delay:{index * 0.1}s;">
            <div class="clip-meta">
                <div style="display:flex; gap:8px; flex-wrap:wrap; margin-bottom:10px;">
                    <span class="clip-badge badge-timestamp">⏱ {timestamp:.1f}s</span>
                    <span class="clip-badge badge-similarity">✓ {sim_pct}%</span>
                    <span class="clip-badge badge-duration">▶ {duration:.1f}s</span>
                </div>
                <div class="sim-bar-track">
                    <div class="sim-bar-fill" style="width:{sim_pct}%;"></div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if clip_bytes is not None:
        st.video(clip_bytes, format="video/mp4")
    elif error_message:
        st.error(error_message)


# ---------------------------------------------------------------------------
# Pages
# ---------------------------------------------------------------------------
def render_admin_page(api_base_url: str) -> None:
    st.markdown('<div class="page-enter">', unsafe_allow_html=True)

    # Header section
    st.markdown(
        """
        <div style="text-align:center; margin-bottom:8px;">
            <div style="font-size:48px; margin-bottom:8px; animation: float 3s ease-in-out infinite;">🎥</div>
            <h2 style="margin:0;">Admin Video Upload</h2>
            <p style="color:var(--text-secondary); margin-top:6px;">
                Upload the source video that will be scanned for face matches.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    render_step_flow(active_step=1)
    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

    # Admin video status
    if st.session_state.get("admin_upload_success"):
        vid = st.session_state.get("admin_video_id", "—")
        st.markdown(
            f"""
            <div class="success-banner celebration">
                <h4>✅ Admin Video Active</h4>
                <p style="color:var(--text-secondary); margin:0; font-size:14px;">
                    Video ID: <code>{vid}</code> — ready for face matching
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown("", unsafe_allow_html=True)

    # Upload card
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown(
        """
        <div class="upload-zone">
            <div class="upload-icon">📤</div>
            <p style="color:var(--text-secondary); margin:0;">
                Drag & drop or browse to select a video file
            </p>
            <p style="color:var(--text-muted); font-size:12px; margin-top:6px;">
                Supported: MP4, MOV, AVI, MKV &nbsp;•&nbsp; Max size: 300 MB
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    admin_video = st.file_uploader(
        "Choose a video file",
        type=["mp4", "mov", "avi", "mkv"],
        key="admin_video_uploader",
        label_visibility="collapsed",
    )

    if admin_video is not None:
        render_file_info(admin_video)

    st.markdown("", unsafe_allow_html=True)

    if st.button("🚀  Upload Admin Video", use_container_width=True):
        if admin_video is None:
            st.error("Please select a video file first.")
            return
        if not _is_allowed_file(
            admin_video,
            allowed_content_types=ALLOWED_ADMIN_VIDEO_CONTENT_TYPES,
            allowed_extensions=ALLOWED_ADMIN_VIDEO_EXTENSIONS,
        ):
            st.error("Invalid file type. Admin upload accepts video files only: mp4, mov, avi, mkv, mpeg.")
            return
        if admin_video.size > MAX_VIDEO_UPLOAD_SIZE_BYTES:
            st.error("Video size exceeds 300 MB limit.")
            return

        with st.spinner("Uploading video…"):
            ok, payload = post_file(
                api_base_url=api_base_url,
                endpoint="/admin-video-upload",
                file_field="file",
                uploaded_file=admin_video,
            )

        if not ok:
            st.error(payload.get("error", "Failed to upload admin video."))
            return

        st.session_state["admin_upload_success"] = True
        st.session_state["admin_video_id"] = payload.get("video_id", "—")

        st.markdown(
            f"""
            <div class="success-banner celebration">
                <h4>🎉 Upload Successful!</h4>
                <p style="color:var(--text-secondary); margin:0; font-size:14px;">
                    Video ID: <code>{payload.get('video_id', '—')}</code>
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        with st.expander("📋 View raw API response"):
            st.json(payload)

    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)


def render_user_page(api_base_url: str) -> None:
    st.markdown('<div class="page-enter">', unsafe_allow_html=True)

    # Header section
    st.markdown(
        """
        <div style="text-align:center; margin-bottom:8px;">
            <div style="font-size:48px; margin-bottom:8px; animation: float 3s ease-in-out infinite;">🧑‍🎤</div>
            <h2 style="margin:0;">Face Match & Clip Generator</h2>
            <p style="color:var(--text-secondary); margin-top:6px;">
                Upload a photo to find matching faces and generate short video clips.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    render_step_flow(active_step=1)
    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

    # Admin video status indicator
    admin_active = st.session_state.get("admin_upload_success", False)
    dot_class = "status-active" if admin_active else "status-inactive"
    label = "Admin video uploaded" if admin_active else "No admin video — upload one first"
    st.markdown(
        f"""
        <div style="margin-bottom:20px; font-size:13px; color:var(--text-secondary);">
            <span class="status-dot {dot_class}"></span>{label}
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Photo upload card
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    col_upload, col_settings = st.columns([3, 2], gap="large")

    with col_upload:
        st.markdown("#### 📸 Your Photo")
        st.markdown(
            """
            <div class="upload-zone" style="padding:32px 24px;">
                <div class="upload-icon" style="font-size:36px;">🖼️</div>
                <p style="color:var(--text-secondary); margin:0; font-size:14px;">
                    Upload a clear face photo
                </p>
                <p style="color:var(--text-muted); font-size:12px; margin-top:4px;">
                    PNG or JPEG • Clear frontal face recommended
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        user_photo = st.file_uploader(
            "Choose a photo",
            type=["jpg", "jpeg", "png"],
            key="user_photo_uploader",
            label_visibility="collapsed",
        )
        if user_photo is not None:
            render_file_info(user_photo)
            st.image(user_photo, caption="Uploaded photo", use_container_width=True)

    with col_settings:
        st.markdown("#### ⚙️ Clip Settings")
        st.markdown(
            '<div style="height:8px;"></div>',
            unsafe_allow_html=True,
        )
        clip_duration = st.slider(
            "Clip Duration (seconds)",
            min_value=3.0,
            max_value=5.0,
            value=4.0,
            step=0.5,
            help="Duration of each generated video clip",
        )
        st.markdown(
            f'<div style="text-align:center; color:var(--accent-secondary); font-weight:600; font-size:20px;">'
            f"{clip_duration:.1f}s</div>",
            unsafe_allow_html=True,
        )
        st.markdown('<div style="height:16px;"></div>', unsafe_allow_html=True)

        max_clips = st.slider(
            "Maximum Clips",
            min_value=1,
            max_value=20,
            value=5,
            step=1,
            help="Maximum number of clips to generate",
        )
        st.markdown(
            f'<div style="text-align:center; color:var(--accent-secondary); font-weight:600; font-size:20px;">'
            f"{max_clips} clips</div>",
            unsafe_allow_html=True,
        )

        # Summary
        st.markdown(
            f"""
            <div class="info-card" style="margin-top:20px;">
                <strong>Summary</strong><br>
                <span style="font-size:13px; color:var(--text-muted);">
                    Up to <strong>{max_clips}</strong> clips × <strong>{clip_duration:.1f}s</strong> each
                </span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("", unsafe_allow_html=True)

    # Generate button
    if st.button("⚡  Generate Matched Clips", use_container_width=True):
        if user_photo is None:
            st.error("Please select a photo file first.")
            return
        if not _is_allowed_file(
            user_photo,
            allowed_content_types=ALLOWED_USER_IMAGE_CONTENT_TYPES,
            allowed_extensions=ALLOWED_USER_IMAGE_EXTENSIONS,
        ):
            st.error("Invalid file type. Upload accepts PNG or JPEG images only.")
            return

        render_step_flow(active_step=2)

        with st.spinner("🔍 Analyzing faces and generating clips — this may take a moment…"):
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

        render_step_flow(active_step=3)

        # Success banner
        clips = payload.get("clips", [])
        user_id = payload.get("user_id", "—")

        st.markdown(
            f"""
            <div class="success-banner celebration">
                <h4>🎉 Clips Generated Successfully!</h4>
                <p style="color:var(--text-secondary); margin:0; font-size:14px;">
                    User ID: <code>{user_id}</code>
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if not clips:
            st.markdown(
                """
                <div class="empty-state">
                    <div class="empty-state-icon">🔍</div>
                    <h3 style="color:var(--text-muted);">No Matches Found</h3>
                    <p style="color:var(--text-muted);">
                        No face matches were found in the admin video.<br>
                        Try uploading a clearer photo or a different angle.
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )
            with st.expander("📋 View raw API response"):
                st.json(payload)
            return

        # Metrics row
        st.markdown('<div style="height:20px;"></div>', unsafe_allow_html=True)
        metric_cols = st.columns(3)
        with metric_cols[0]:
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-value">{len(clips)}</div>
                    <div class="metric-label">Clips Found</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with metric_cols[1]:
            avg_sim = sum(c.get("similarity", 0) for c in clips) / len(clips) if clips else 0
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-value">{avg_sim * 100:.1f}%</div>
                    <div class="metric-label">Avg Similarity</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with metric_cols[2]:
            total_dur = sum(c.get("duration", 0) for c in clips)
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-value">{total_dur:.1f}s</div>
                    <div class="metric-label">Total Duration</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        # Clip grid
        st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
        st.markdown("### 🎬 Generated Clips")

        # Display clips in a 2-column grid
        for row_start in range(0, len(clips), 2):
            row_clips = clips[row_start : row_start + 2]
            cols = st.columns(len(row_clips))
            for col_idx, clip in enumerate(row_clips):
                with cols[col_idx]:
                    clip_path = clip.get("clip", "")
                    clip_bytes_data: bytes | None = None
                    clip_error: str | None = None
                    if clip_path:
                        clip_url = f"{api_base_url.rstrip('/')}/clip-file?path={quote(clip_path)}"
                        clip_ok, clip_bytes_data, clip_error = fetch_binary(clip_url)
                        if not clip_ok:
                            clip_bytes_data = None
                    render_clip_card(
                        index=row_start + col_idx,
                        clip=clip,
                        clip_bytes=clip_bytes_data,
                        error_message=clip_error,
                    )

        # Raw response
        with st.expander("📋 View raw API response"):
            st.json(payload)

    st.markdown("</div>", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    st.set_page_config(
        page_title="Face Match Video Generator",
        page_icon="🎬",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    inject_custom_css()

    # Sidebar
    with st.sidebar:
        st.markdown(
            """
            <div style="text-align:center; padding:16px 0 24px;">
                <div style="font-size:36px; margin-bottom:8px;">🎬</div>
                <h3 style="margin:0; font-size:18px; background:var(--accent-gradient);
                    -webkit-background-clip:text; -webkit-text-fill-color:transparent;
                    background-clip:text;">
                    Face Match
                </h3>
                <p style="color:var(--text-muted); font-size:11px; margin-top:4px; letter-spacing:1px;">
                    VIDEO GENERATOR
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

        page = st.radio(
            "Navigation",
            options=["🎥  Admin Upload", "🧑‍🎤  Face Match"],
            index=0,
            label_visibility="collapsed",
        )

        st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

        api_base_url = st.text_input(
            "🔗 API Base URL",
            value=DEFAULT_API_BASE_URL,
        )
        if "127.0.0.1" in api_base_url or "localhost" in api_base_url:
            st.caption(
                "⚠️ Using local API URL — only works when Streamlit and FastAPI run on the same machine."
            )

        # Status
        st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
        admin_active = st.session_state.get("admin_upload_success", False)
        dot_class = "status-active" if admin_active else "status-inactive"
        status_text = "Video uploaded ✓" if admin_active else "No video uploaded"
        st.markdown(
            f"""
            <div style="font-size:12px; color:var(--text-muted); padding:4px 0;">
                <span class="status-dot {dot_class}"></span>
                Admin: {status_text}
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Footer
        st.markdown(
            """
            <div style="position:fixed; bottom:16px; left:16px; right:16px;
                         font-size:11px; color:var(--text-muted); text-align:center;">
                Built with ❤️ using Streamlit + FastAPI
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Title
    st.markdown(
        """
        <h1 style="text-align:center; font-size:2.2rem; margin-bottom:4px; animation: fadeSlideUp 0.6s ease-out;">
            Face Match Video Generator
        </h1>
        <p style="text-align:center; color:var(--text-secondary); font-size:15px; margin-bottom:32px;
                  animation: fadeSlideUp 0.8s ease-out;">
            AI-powered face matching &amp; clip generation from source video footage
        </p>
        """,
        unsafe_allow_html=True,
    )

    # Route pages
    if "Admin" in (page or ""):
        render_admin_page(api_base_url)
    else:
        render_user_page(api_base_url)


if __name__ == "__main__":
    main()
