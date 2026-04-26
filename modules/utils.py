import json
import io
import os
import re
import streamlit as st
from gtts import gTTS

from modules.config import PROGRESS_FILE, PERSISTED_KEYS, PERSISTED_SET_KEYS, APP_DIR


def get_file_signature(file_path):
    if not os.path.exists(file_path):
        return None
    stat = os.stat(file_path)
    return stat.st_mtime_ns, stat.st_size


def save_progress():
    payload = {}
    for key in PERSISTED_KEYS:
        payload[key] = to_json_safe(st.session_state.get(key))
    with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def load_progress():
    if not os.path.exists(PROGRESS_FILE):
        return
    try:
        with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
            payload = json.load(f)
    except (OSError, json.JSONDecodeError):
        return
    for key in PERSISTED_KEYS:
        if key not in payload:
            continue
        value = payload[key]
        if key in PERSISTED_SET_KEYS:
            st.session_state[key] = set(value)
        else:
            st.session_state[key] = value


def to_json_safe(value):
    if isinstance(value, set):
        return [to_json_safe(item) for item in sorted(value)]
    if hasattr(value, "item"):
        try:
            return value.item()
        except (TypeError, ValueError):
            pass
    return value


def rerun_app():
    save_progress()
    st.rerun()


@st.cache_data(show_spinner=False)
def get_audio_bytes(text: str, lang: str = "zh") -> bytes:
    if not text or not isinstance(text, str):
        return b""
    try:
        clean = re.sub(r'_+', ' ', text)
        clean = re.sub(r'\s+', ' ', clean).strip()
        tts = gTTS(text=clean, lang=lang, slow=False)
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)
        return fp.read()
    except Exception:
        return b""


def render_speaker_button(text: str, key_suffix: str, lang: str = "zh"):
    if st.button("🔊", key=f"speak_{key_suffix}", help="Dengarkan suara"):
        audio_bytes = get_audio_bytes(text, lang)
        if audio_bytes:
            st.audio(audio_bytes, format="audio/mp3", autoplay=True)
        else:
            st.warning("Tidak dapat menghasilkan suara.")


def validate_required_columns(sheet_name, df, required_columns):
    missing = [col for col in required_columns if col not in df.columns]
    if not missing:
        return None
    return f"Sheet '{sheet_name}' wajib punya kolom: {', '.join(required_columns)}. Kolom yang belum ada: {', '.join(missing)}."


def get_theme_css():
    if st.session_state.get("theme_mode", "Terang") == "Terang":
        return """
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:opsz,wght@14..32,300;14..32,500;14..32,700;14..32,800&display=swap');
            * { font-family: 'Inter', sans-serif; }
            .stApp { background: radial-gradient(circle at 10% 30%, #f9faff, #eef2ff); backdrop-filter: blur(2px); }
            [data-testid="stSidebar"] { background: rgba(255, 255, 255, 0.6); backdrop-filter: blur(20px); border-right: 1px solid rgba(255,255,255,0.5); }
            .glass-card { background: rgba(255, 255, 255, 0.85); backdrop-filter: blur(16px); border-radius: 38px; padding: 28px 24px; border: 1px solid rgba(255,255,255,0.6); box-shadow: 0 20px 35px -12px rgba(0,0,0,0.05); margin-bottom: 1rem; }
            .glass-soft { background: rgba(255, 255, 255, 0.72); backdrop-filter: blur(12px); border-radius: 26px; padding: 18px 18px; border: 1px solid rgba(255,255,255,0.75); box-shadow: 0 12px 22px -16px rgba(0,0,0,0.08); margin-bottom: 1rem; }
            .hanzi-giant { font-size: clamp(3.5rem, 12vw, 7rem); font-weight: 800; letter-spacing: 2px; background: linear-gradient(135deg, #1e2b6e, #2b3f8e); -webkit-background-clip: text; background-clip: text; color: transparent; text-align: center; }
            .pinyin-chip { background: rgba(59,130,246,0.15); border-radius: 60px; padding: 6px 18px; font-weight: 500; font-size: 0.9rem; color: #1e40af; display: inline-block; backdrop-filter: blur(4px); }
            div.stButton > button { background: white; border: none; border-radius: 48px; padding: 12px 16px; font-weight: 600; font-size: 0.9rem; transition: all 0.25s ease; box-shadow: 0 1px 2px rgba(0,0,0,0.02); border: 1px solid rgba(0,0,0,0.04); width: 100%; color: #1e293b; }
            div.stButton > button:hover { transform: translateY(-3px); box-shadow: 0 12px 22px -12px rgba(59,130,246,0.3); border-color: #3b82f6; background: #fafcff; }
            .grid-floating button { background: rgba(255,255,240,0.7); backdrop-filter: blur(8px); border: 1px solid rgba(255,255,255,0.8); color: #1e293b; }
            .sidebar-title, .stSidebar .stMarkdown, .stSidebar .stCaption { color: #1e293b; }
            .score-modern { background: linear-gradient(105deg, #3b82f6, #2563eb); color: white; border-radius: 28px; padding: 20px; margin-bottom: 12px; }
            .mini-stat { border-radius: 24px; padding: 16px 18px; background: rgba(255,255,255,0.76); border: 1px solid rgba(255,255,255,0.7); box-shadow: 0 10px 18px -14px rgba(0,0,0,0.12); }
            .mini-stat-label { font-size: 0.78rem; color: #64748b; text-transform: uppercase; letter-spacing: 0.08em; }
            .mini-stat-value { font-size: 1.6rem; font-weight: 800; color: #1e293b; }
            .hint-box { border-left: 4px solid #3b82f6; padding: 12px 14px; border-radius: 16px; background: rgba(59,130,246,0.08); color: #1e293b; }
            .stProgress > div > div > div > div { background: linear-gradient(90deg, #3b82f6, #2563eb); }
            .stAlert, .stSuccess, .stError, .stInfo { background-color: rgba(255,255,255,0.9); color: #1e293b; }
            @media (max-width: 768px) {
                .hanzi-giant { font-size: 2.5rem !important; }
                .glass-card, .glass-soft, .glass-card p, .glass-card div, .glass-card span { color: #1e293b !important; }
                div.stButton > button { font-size: 0.85rem !important; padding: 8px 12px !important; background: white !important; color: #1e293b !important; }
                [data-testid="stSidebar"] { background: rgba(255, 255, 255, 0.95) !important; }
            }
        </style>
        """
    else:
        return """
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:opsz,wght@14..32,300;14..32,500;14..32,700;14..32,800&display=swap');
            * { font-family: 'Inter', sans-serif; }
            .stApp { background: #0f172a; backdrop-filter: blur(2px); }
            [data-testid="stSidebar"] { background: rgba(15, 23, 42, 0.8); backdrop-filter: blur(20px); border-right: 1px solid rgba(255,255,255,0.1); }
            .glass-card { background: rgba(30, 41, 59, 0.85); backdrop-filter: blur(16px); border-radius: 38px; padding: 28px 24px; border: 1px solid rgba(255,255,255,0.1); box-shadow: 0 20px 35px -12px rgba(0,0,0,0.3); margin-bottom: 1rem; }
            .glass-soft { background: rgba(30, 41, 59, 0.7); backdrop-filter: blur(12px); border-radius: 26px; padding: 18px 18px; border: 1px solid rgba(255,255,255,0.1); box-shadow: 0 12px 22px -16px rgba(0,0,0,0.3); margin-bottom: 1rem; }
            .hanzi-giant { font-size: clamp(3.5rem, 12vw, 7rem); font-weight: 800; letter-spacing: 2px; background: linear-gradient(135deg, #b0c4ff, #8aadff); -webkit-background-clip: text; background-clip: text; color: transparent; text-align: center; }
            .pinyin-chip { background: rgba(100,150,255,0.2); border-radius: 60px; padding: 6px 18px; font-weight: 500; font-size: 0.9rem; color: #aac8ff; display: inline-block; backdrop-filter: blur(4px); }
            div.stButton > button { background: #1e293b; border: 1px solid #334155; border-radius: 48px; padding: 12px 16px; font-weight: 600; font-size: 0.9rem; transition: all 0.25s ease; width: 100%; color: #f1f5f9; }
            div.stButton > button:hover { transform: translateY(-3px); box-shadow: 0 12px 22px -12px #3b82f6; border-color: #3b82f6; background: #283548; color: white; }
            .grid-floating button { background: #1e293b; backdrop-filter: blur(8px); border: 1px solid #334155; color: #f1f5f9; }
            .sidebar-title, .stSidebar .stMarkdown, .stSidebar .stCaption { color: #e2e8f0; }
            .score-modern { background: linear-gradient(105deg, #1e40af, #3b82f6); color: white; border-radius: 28px; padding: 20px; margin-bottom: 12px; }
            .mini-stat { border-radius: 24px; padding: 16px 18px; background: rgba(30,41,59,0.78); border: 1px solid rgba(255,255,255,0.08); box-shadow: 0 10px 18px -14px rgba(0,0,0,0.4); }
            .mini-stat-label { font-size: 0.78rem; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.08em; }
            .mini-stat-value { font-size: 1.6rem; font-weight: 800; color: #f8fafc; }
            .hint-box { border-left: 4px solid #60a5fa; padding: 12px 14px; border-radius: 16px; background: rgba(59,130,246,0.12); color: #e2e8f0; }
            .stProgress > div > div > div > div { background: linear-gradient(90deg, #3b82f6, #60a5fa); }
            .stAlert, .stSuccess, .stError, .stInfo { background-color: #1e293b; color: #f1f5f9; border: 1px solid #334155; }
            .stSuccess { background-color: #0f3b1f; color: #bef264; }
            .stError { background-color: #4a0f1a; color: #fecaca; }
            .stInfo { background-color: #0f2f4a; color: #b0d4ff; }
            @media (max-width: 768px) {
                .hanzi-giant { font-size: 2.5rem !important; }
                .glass-card, .glass-soft, .glass-card p, .glass-card div, .glass-card span { color: #e2e8f0 !important; }
                div.stButton > button { font-size: 0.85rem !important; padding: 8px 12px !important; background: #1e293b !important; color: #f1f5f9 !important; }
                [data-testid="stSidebar"] { background: rgba(15, 23, 42, 0.95) !important; }
            }
        </style>
        """


def render_top_dashboard(vocab_df, mastered_vocab, total_score_func, accuracy_func, current_streak, total_vocab):
    """Menampilkan dashboard di atas setiap halaman"""
    progress_done = len(mastered_vocab)
    progress_ratio = progress_done / total_vocab if total_vocab else 0

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"<div class='mini-stat'><div class='mini-stat-label'>Total Skor</div><div class='mini-stat-value'>{total_score_func()}</div></div>", unsafe_allow_html=True)
    with col2:
        st.markdown(f"<div class='mini-stat'><div class='mini-stat-label'>Akurasi</div><div class='mini-stat-value'>{accuracy_func()}%</div></div>", unsafe_allow_html=True)
    with col3:
        st.markdown(f"<div class='mini-stat'><div class='mini-stat-label'>Streak</div><div class='mini-stat-value'>{current_streak}</div></div>", unsafe_allow_html=True)
    with col4:
        st.markdown(f"<div class='mini-stat'><div class='mini-stat-label'>Dikuasai</div><div class='mini-stat-value'>{progress_done}/{total_vocab}</div></div>", unsafe_allow_html=True)

    left, right = st.columns([2, 1])
    with left:
        st.markdown("<div class='glass-soft'><strong>Progress Kosakata</strong></div>", unsafe_allow_html=True)
        st.progress(progress_ratio)
        st.caption(f"{progress_done} dari {total_vocab} kosakata sudah ditandai dikuasai.")
    with right:
        daily_target = st.session_state.get("daily_target", 30)
        total_attempts = st.session_state.get("quiz_attempts", 0) + st.session_state.get("cloze_attempts", 0) + st.session_state.get("scramble_attempts", 0)
        target_ratio = min(total_attempts / max(daily_target, 1), 1.0)
        st.markdown("<div class='glass-soft'><strong>Target Harian</strong></div>", unsafe_allow_html=True)
        st.progress(target_ratio)
        st.caption(f"{total_attempts} / {daily_target} latihan hari ini")