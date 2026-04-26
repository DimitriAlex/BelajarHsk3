import json
import os
import random
from copy import deepcopy

import jieba
import pandas as pd
import streamlit as st
from gtts import gTTS
import io
import re

native_rerun = st.rerun

st.set_page_config(
    page_title="HSK 3 Master | Modern Learning",
    page_icon="✅",
    layout="wide",
    initial_sidebar_state="expanded",
)

APP_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(APP_DIR, "hsk3.xlsx")
PROGRESS_FILE = os.path.join(APP_DIR, "progress.json")
AVATAR_OPTIONS = ["😀", "😎", "🤓", "🧐", "🎯", "🌟", "📚", "🚀"]
PERSISTED_SET_KEYS = {
    "quiz_answered_set",
    "cloze_answered_set",
    "scramble_scored_set",
    "wrong_quiz",
    "wrong_cloze",
    "wrong_scramble",
    "favorites",
    "mastered_vocab",
}
PERSISTED_KEYS = [
    "profile_name",
    "profile_avatar",
    "theme_mode",
    "menu",
    "fc_page",
    "selected_hanzi",
    "score_quiz",
    "score_cloze",
    "score_scramble",
    "quiz_answered_set",
    "cloze_answered_set",
    "scramble_scored_set",
    "wrong_quiz",
    "wrong_cloze",
    "wrong_scramble",
    "rep_mode",
    "quiz_idx",
    "quiz_mode",
    "clz_idx",
    "sc_idx",
    "flashcard_search",
    "hide_mastered",
    "favorites",
    "mastered_vocab",
    "daily_target",
    "current_streak",
    "best_streak",
    "quiz_attempts",
    "quiz_correct_attempts",
    "cloze_attempts",
    "cloze_correct_attempts",
    "scramble_attempts",
    "scramble_correct_attempts",
]

def get_file_signature(file_path):
    if not os.path.exists(file_path):
        return None
    stat = os.stat(file_path)
    return stat.st_mtime_ns, stat.st_size

def validate_required_columns(sheet_name, df, required_columns):
    missing = [col for col in required_columns if col not in df.columns]
    if not missing:
        return None
    return f"Sheet '{sheet_name}' wajib punya kolom: {', '.join(required_columns)}. Kolom yang belum ada: {', '.join(missing)}."

def load_progress():
    if not os.path.exists(PROGRESS_FILE): return
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

def save_progress():
    payload = {}
    for key in PERSISTED_KEYS:
        payload[key] = to_json_safe(st.session_state.get(key))
    with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

def rerun_app():
    save_progress()
    native_rerun()

def profile_is_complete():
    return bool(str(st.session_state.profile_name).strip() and st.session_state.profile_avatar)

def init_state():
    defaults = {
        "profile_name": "",
        "profile_avatar": "",
        "theme_mode": "Terang",
        "menu": "📇 Flashcard",
        "fc_page": 0,
        "selected_hanzi": None,
        "score_quiz": 0,
        "score_cloze": 0,
        "score_scramble": 0,
        "quiz_answered_set": set(),
        "cloze_answered_set": set(),
        "scramble_scored_set": set(),
        "wrong_quiz": set(),
        "wrong_cloze": set(),
        "wrong_scramble": set(),
        "rep_mode": "Normal",
        "quiz_idx": 0,
        "quiz_options": [],
        "quiz_answered": False,
        "quiz_show_pinyin": False,
        "quiz_mode": "Hanzi → Arti",
        "quiz_feedback": None,
        "clz_idx": 0,
        "clz_options": [],
        "clz_answered": False,
        "clz_show_pinyin": False,
        "clz_feedback": None,
        "sc_idx": 0,
        "sc_tokens": [],
        "sc_order": [],
        "sc_original": [],
        "sc_answered": False,
        "sc_feedback": None,
        "flashcard_search": "",
        "hide_mastered": True,
        "favorites": set(),
        "mastered_vocab": set(),
        "daily_target": 30,
        "current_streak": 0,
        "best_streak": 0,
        "quiz_attempts": 0,
        "quiz_correct_attempts": 0,
        "cloze_attempts": 0,
        "cloze_correct_attempts": 0,
        "scramble_attempts": 0,
        "scramble_correct_attempts": 0,
        "_progress_loaded": False,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_state()
if not st.session_state._progress_loaded:
    load_progress()
    st.session_state._progress_loaded = True

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

def get_theme_css():
    if st.session_state.theme_mode == "Terang":
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

st.markdown(get_theme_css(), unsafe_allow_html=True)

@st.cache_data
def load_data(file_path, file_signature):
    del file_signature
    if not os.path.exists(file_path):
        return None, None, None, "File hsk3.xlsx tidak ditemukan."
    try:
        vocab_df = pd.read_excel(file_path, sheet_name="Kosa_kata")
        cloze_df = pd.read_excel(file_path, sheet_name="Kalimat_kosong")
        scramble_df = pd.read_excel(file_path, sheet_name="Acak")
    except Exception as exc:
        return None, None, None, f"Gagal membaca file Excel: {exc}"
    required_vocab = ["Kosakata", "Pinyin", "Arti Indonesia"]
    required_cloze = ["kalimat", "jawaban_benar", "pilihan1", "pilihan2", "pilihan3", "pilihan4"]
    required_scramble = ["kalimat_asli"]
    for sheet_name, df, req in [("Kosa_kata", vocab_df, required_vocab),
                                 ("Kalimat_kosong", cloze_df, required_cloze),
                                 ("Acak", scramble_df, required_scramble)]:
        error = validate_required_columns(sheet_name, df, req)
        if error:
            return None, None, None, error
    return vocab_df.fillna(""), cloze_df.fillna(""), scramble_df.fillna(""), None

vocab, cloze, scramble, load_error = load_data(DATA_FILE, get_file_signature(DATA_FILE))
if load_error:
    st.error(load_error)
    st.stop()
total_vocab = len(vocab)

def total_score():
    return st.session_state.score_quiz + st.session_state.score_cloze + st.session_state.score_scramble

def total_attempts():
    return st.session_state.quiz_attempts + st.session_state.cloze_attempts + st.session_state.scramble_attempts

def total_correct_attempts():
    return st.session_state.quiz_correct_attempts + st.session_state.cloze_correct_attempts + st.session_state.scramble_correct_attempts

def accuracy_percent():
    att = total_attempts()
    if att == 0: return 0
    return round((total_correct_attempts() / att) * 100)

def update_streak(is_correct):
    if is_correct:
        st.session_state.current_streak += 1
        st.session_state.best_streak = max(st.session_state.best_streak, st.session_state.current_streak)
    else:
        st.session_state.current_streak = 0

def reset_scores():
    for key in ["score_quiz", "score_cloze", "score_scramble"]:
        st.session_state[key] = 0
    for key in ["quiz_attempts", "quiz_correct_attempts", "cloze_attempts", "cloze_correct_attempts",
                "scramble_attempts", "scramble_correct_attempts", "current_streak", "best_streak"]:
        st.session_state[key] = 0
    for key in ["quiz_answered_set", "cloze_answered_set", "scramble_scored_set", "wrong_quiz", "wrong_cloze", "wrong_scramble"]:
        st.session_state[key].clear()

def render_top_dashboard():
    progress_done = len(st.session_state.mastered_vocab)
    progress_ratio = progress_done / total_vocab if total_vocab else 0
    target_ratio = min(total_attempts() / max(st.session_state.daily_target, 1), 1.0)
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"<div class='mini-stat'><div class='mini-stat-label'>Total Skor</div><div class='mini-stat-value'>{total_score()}</div></div>", unsafe_allow_html=True)
    with col2:
        st.markdown(f"<div class='mini-stat'><div class='mini-stat-label'>Akurasi</div><div class='mini-stat-value'>{accuracy_percent()}%</div></div>", unsafe_allow_html=True)
    with col3:
        st.markdown(f"<div class='mini-stat'><div class='mini-stat-label'>Streak</div><div class='mini-stat-value'>{st.session_state.current_streak}</div></div>", unsafe_allow_html=True)
    with col4:
        st.markdown(f"<div class='mini-stat'><div class='mini-stat-label'>Dikuasai</div><div class='mini-stat-value'>{progress_done}/{total_vocab}</div></div>", unsafe_allow_html=True)
    left, right = st.columns([2,1])
    with left:
        st.markdown("<div class='glass-soft'><strong>Progress Kosakata</strong></div>", unsafe_allow_html=True)
        st.progress(progress_ratio)
        st.caption(f"{progress_done} dari {total_vocab} kosakata sudah ditandai dikuasai.")
    with right:
        st.markdown("<div class='glass-soft'><strong>Target Harian</strong></div>", unsafe_allow_html=True)
        st.progress(target_ratio)
        st.caption(f"{total_attempts()} / {st.session_state.daily_target} latihan hari ini")

def build_quiz_pool(total, wrong_set):
    if st.session_state.rep_mode == "Soal Salah Saja":
        if wrong_set:
            return list(wrong_set)
        st.info("Semua soal di mode ini sudah beres. Kembali ke mode Normal.")
        st.session_state.rep_mode = "Normal"
        rerun_app()
    return list(range(total))

def build_flashcard_indices():
    search_text = st.session_state.flashcard_search.strip().lower()
    result = []
    for idx, row in vocab.iterrows():
        haystack = " ".join([str(row.get("Kosakata","")), str(row.get("Pinyin","")), str(row.get("Arti Indonesia","")), str(row.get("Contoh",""))]).lower()
        if search_text and search_text not in haystack:
            continue
        if st.session_state.hide_mastered and idx in st.session_state.mastered_vocab:
            continue
        result.append(idx)
    return result

def render_profile_setup():
    st.markdown("""<div class='glass-card' style='text-align:center'><h1>Mulai Belajar HSK 3</h1><p>Isi username dan pilih avatar.</p></div>""", unsafe_allow_html=True)
    _, center, _ = st.columns([1,1.5,1])
    with center:
        with st.form("profile_setup_form"):
            username = st.text_input("Username", value=st.session_state.profile_name, max_chars=24, placeholder="mis. Alex")
            current_avatar = st.session_state.profile_avatar or AVATAR_OPTIONS[0]
            avatar_index = AVATAR_OPTIONS.index(current_avatar) if current_avatar in AVATAR_OPTIONS else 0
            avatar = st.radio("Pilih avatar", AVATAR_OPTIONS, index=avatar_index, horizontal=True)
            submitted = st.form_submit_button("Masuk dan simpan progress", type="primary", use_container_width=True)
        if submitted:
            clean = username.strip()
            if not clean:
                st.error("Username wajib diisi.")
            else:
                st.session_state.profile_name = clean
                st.session_state.profile_avatar = avatar
                rerun_app()

def render_sidebar_profile():
    st.markdown(f"""<div class="glass-soft" style="text-align:center"><div style="font-size:2rem">{st.session_state.profile_avatar}</div><div style="font-weight:800">{st.session_state.profile_name}</div><div style="font-size:0.85rem">Progress tersimpan otomatis</div></div>""", unsafe_allow_html=True)
    with st.expander("Ubah profil", expanded=False):
        with st.form("profile_sidebar_form"):
            username = st.text_input("Username", value=st.session_state.profile_name, max_chars=24, key="profile_sidebar_name")
            avatar_index = AVATAR_OPTIONS.index(st.session_state.profile_avatar) if st.session_state.profile_avatar in AVATAR_OPTIONS else 0
            avatar = st.radio("Avatar", AVATAR_OPTIONS, index=avatar_index, horizontal=True, key="profile_sidebar_avatar")
            submitted = st.form_submit_button("Simpan profil", use_container_width=True)
        if submitted:
            clean = username.strip()
            if not clean:
                st.error("Username wajib diisi.")
            else:
                st.session_state.profile_name = clean
                st.session_state.profile_avatar = avatar
                rerun_app()

# ==================== SIDEBAR ====================
with st.sidebar:
    if profile_is_complete():
        render_sidebar_profile()
    else:
        st.markdown("""<div class='glass-soft'><strong>Siapkan profil belajar</strong><p>Isi username dan pilih avatar di halaman utama.</p></div>""", unsafe_allow_html=True)
    st.markdown(f"""<div class="score-modern"><span>TOTAL SCORE</span><br><span style="font-size:2.2rem">{total_score()}</span></div>""", unsafe_allow_html=True)
    st.markdown("<div class='sidebar-title'>📌 Menu</div>", unsafe_allow_html=True)
    for label in ["📇 Flashcard", "📝 Kuis Kosakata", "✏️ Isi Kalimat", "🔄 Susun Kalimat"]:
        if st.button(label, key=f"menu_{label}", use_container_width=True):
            st.session_state.menu = label
            st.session_state.selected_hanzi = None
            rerun_app()
    if st.button("📝 Latihan H31003", key="menu_h31003", use_container_width=True):
        st.session_state.menu = "H31003 Exam"
        st.session_state.selected_hanzi = None
        rerun_app()
    st.divider()
    if st.button("🗑️ Reset seluruh skor", use_container_width=True):
        reset_scores()
        rerun_app()
    st.caption(f"Quiz: {st.session_state.score_quiz}")
    st.caption(f"Isi Kalimat: {st.session_state.score_cloze}")
    st.caption(f"Susun: {st.session_state.score_scramble}")
    st.caption(f"Favorit: {len(st.session_state.favorites)}")
    st.markdown("### 🎯 Mode Latihan")
    rep_mode = st.radio("Pilih mode", ["Normal", "Soal Salah Saja"], index=0 if st.session_state.rep_mode=="Normal" else 1, key="rep_mode_radio")
    if rep_mode != st.session_state.rep_mode:
        st.session_state.rep_mode = rep_mode
        st.session_state.quiz_options = []
        st.session_state.clz_options = []
        st.session_state.quiz_answered = False
        st.session_state.clz_answered = False
        rerun_app()
    st.markdown("### 🎯 Target Harian")
    daily_target = st.slider("Jumlah latihan", 10, 100, st.session_state.daily_target, 5)
    st.session_state.daily_target = daily_target
    st.markdown("### 🎨 Tampilan")
    theme_mode = st.radio("Mode warna", ["Terang", "Gelap"], index=0 if st.session_state.theme_mode=="Terang" else 1, key="theme_radio")
    if theme_mode != st.session_state.theme_mode:
        st.session_state.theme_mode = theme_mode
        rerun_app()

# ==================== FUNGSI VIEW ====================
def flashcard_view():
    st.markdown("<div class='glass-card'><h2>📇 Flashcard</h2><p>Cari kosakata, tandai favorit, lalu simpan yang sudah dikuasai.</p></div>", unsafe_allow_html=True)
    render_top_dashboard()
    search_col, info_col = st.columns([2,1])
    with search_col:
        search_value = st.text_input("Cari Hanzi / Pinyin / Arti", value=st.session_state.flashcard_search, placeholder="mis. 学校 / xuexiao / sekolah")
        if search_value != st.session_state.flashcard_search:
            st.session_state.flashcard_search = search_value
            st.session_state.fc_page = 0
            rerun_app()
    with info_col:
        hide_mastered = st.toggle("Sembunyikan yang dikuasai", value=st.session_state.hide_mastered)
        if hide_mastered != st.session_state.hide_mastered:
            st.session_state.hide_mastered = hide_mastered
            st.session_state.fc_page = 0
            rerun_app()
        st.markdown(f"<div class='hint-box'>Favorit: {len(st.session_state.favorites)}<br>Dikuasai: {len(st.session_state.mastered_vocab)}</div>", unsafe_allow_html=True)
    visible_indices = build_flashcard_indices()
    if not visible_indices:
        st.info("Tidak ada flashcard yang cocok.")
        if st.button("Reset pencarian"):
            st.session_state.flashcard_search = ""
            st.session_state.fc_page = 0
            rerun_app()
        if st.session_state.hide_mastered and st.button("Tampilkan yang dikuasai"):
            st.session_state.hide_mastered = False
            st.session_state.fc_page = 0
            rerun_app()
        return
    per_page = 24
    total_pages = (len(visible_indices)-1)//per_page + 1
    st.session_state.fc_page = min(st.session_state.fc_page, max(total_pages-1,0))
    start = st.session_state.fc_page * per_page
    current_page = visible_indices[start:start+per_page]
    col1, col2, col3 = st.columns([1,2,1])
    with col1:
        if st.button("◀", disabled=st.session_state.fc_page==0):
            st.session_state.fc_page -= 1
            rerun_app()
    with col2:
        st.markdown(f"<div style='text-align:center'>Halaman {st.session_state.fc_page+1} / {total_pages}</div>", unsafe_allow_html=True)
    with col3:
        if st.button("▶", disabled=st.session_state.fc_page>=total_pages-1):
            st.session_state.fc_page += 1
            rerun_app()
    if st.session_state.selected_hanzi is None:
        st.markdown('<div class="grid-floating">', unsafe_allow_html=True)
        cols = st.columns(4)
        for pos, idx in enumerate(current_page):
            row = vocab.iloc[idx]
            label = row["Kosakata"]
            if idx in st.session_state.favorites:
                label = f"⭐ {label}"
            with cols[pos%4]:
                if st.button(label, key=f"fc_{idx}", use_container_width=True):
                    st.session_state.selected_hanzi = idx
                    rerun_app()
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        idx = st.session_state.selected_hanzi
        item = vocab.iloc[idx]
        example = item["Contoh"] if item["Contoh"] else "Belum ada contoh kalimat."
        st.markdown(f"""<div class="glass-card" style="text-align:center"><div class="hanzi-giant">{item['Kosakata']}</div><div><span class="pinyin-chip">{item['Pinyin']}</span></div><hr><p style="font-weight:700; margin:0">Arti</p><p>{item['Arti Indonesia']}</p><p style="font-weight:500">Contoh</p><p>{example}</p></div>""", unsafe_allow_html=True)
        col_spk1, col_spk2 = st.columns([1,1])
        with col_spk1:
            render_speaker_button(item['Kosakata'], f"fc_hanzi_{idx}")
        with col_spk2:
            if example and example != "Belum ada contoh kalimat.":
                render_speaker_button(example, f"fc_contoh_{idx}")
        btn1, btn2, btn3 = st.columns(3)
        with btn1:
            if st.button("⭐ Simpan Favorit" if idx not in st.session_state.favorites else "✅ Favorit Tersimpan", use_container_width=True):
                st.session_state.favorites.add(idx)
                rerun_app()
        with btn2:
            if st.button("✔️ Tandai Dikuasai" if idx not in st.session_state.mastered_vocab else "✅ Sudah Dikuasai", use_container_width=True):
                st.session_state.mastered_vocab.add(idx)
                st.session_state.selected_hanzi = None
                rerun_app()
        with btn3:
            if st.button("⬅ Kembali ke daftar", use_container_width=True):
                st.session_state.selected_hanzi = None
                rerun_app()

def kuis_view():
    st.markdown("<div class='glass-card'><h2>📝 Kuis Kosakata</h2><p>Pilih arti yang tepat.</p></div>", unsafe_allow_html=True)
    render_top_dashboard()
    mode = st.radio("Pilih mode", ["Hanzi → Arti", "Arti → Hanzi"], horizontal=True)
    if mode != st.session_state.quiz_mode:
        st.session_state.quiz_mode = mode
        st.session_state.quiz_options = []
        st.session_state.quiz_answered = False
        st.session_state.quiz_feedback = None
        rerun_app()
    if total_vocab == 0: return
    pool = build_quiz_pool(total_vocab, st.session_state.wrong_quiz)
    if not pool: return
    idx = st.session_state.quiz_idx % len(pool)
    question_idx = pool[idx]
    item = vocab.iloc[question_idx]
    if not st.session_state.quiz_options:
        if st.session_state.quiz_mode == "Hanzi → Arti":
            soal = item["Kosakata"]
            benar = item["Arti Indonesia"]
            candidate_col = "Arti Indonesia"
        else:
            soal = item["Arti Indonesia"]
            benar = item["Kosakata"]
            candidate_col = "Kosakata"
        other_indices = [i for i in range(total_vocab) if i != question_idx]
        random.shuffle(other_indices)
        others = []
        for i in other_indices:
            val = vocab.iloc[i][candidate_col]
            if val != benar and val not in others:
                others.append(val)
            if len(others) == 3: break
        while len(others) < 3:
            others.append("???")
        pilihan = [benar] + others
        random.shuffle(pilihan)
        st.session_state.quiz_options = pilihan
        st.session_state.quiz_answered = False
        st.session_state.quiz_feedback = None
        st.session_state.current_soal = soal
        st.session_state.current_benar = benar
        st.session_state.current_pinyin = item["Pinyin"]
        st.session_state.current_arti = item["Arti Indonesia"]
        st.session_state.current_contoh = item.get("Contoh","")
        st.session_state.current_item = item
    st.progress((idx+1)/len(pool))
    st.caption(f"Soal {idx+1} dari {len(pool)} | Streak {st.session_state.current_streak}")
    col_soal, col_spk = st.columns([4,1])
    with col_soal:
        st.markdown(f"<div class='hanzi-giant'>{st.session_state.current_soal}</div>", unsafe_allow_html=True)
    with col_spk:
        render_speaker_button(st.session_state.current_soal, f"quiz_soal_{question_idx}")
    if st.button("🔊 Tampilkan Pinyin", key="quiz_pin"):
        st.session_state.quiz_show_pinyin = not st.session_state.quiz_show_pinyin
        rerun_app()
    if st.session_state.quiz_show_pinyin:
        st.markdown(f"<div style='text-align:center'><span class='pinyin-chip'>{st.session_state.current_pinyin}</span></div>", unsafe_allow_html=True)
    if not st.session_state.quiz_answered:
        cols = st.columns(2)
        for i, opt in enumerate(st.session_state.quiz_options):
            with cols[i%2]:
                col_btn, col_opt_spk = st.columns([4,1])
                with col_btn:
                    if st.button(opt, key=f"quiz_{question_idx}_{i}", use_container_width=True):
                        st.session_state.quiz_answered = True
                        st.session_state.quiz_attempts += 1
                        is_correct = opt == st.session_state.current_benar
                        st.session_state.user_answer = opt
                        if is_correct:
                            st.session_state.quiz_correct_attempts += 1
                            if question_idx not in st.session_state.quiz_answered_set:
                                st.session_state.score_quiz += 10
                                st.session_state.quiz_answered_set.add(question_idx)
                            st.session_state.wrong_quiz.discard(question_idx)
                            st.session_state.quiz_feedback = "correct"
                        else:
                            st.session_state.wrong_quiz.add(question_idx)
                            st.session_state.quiz_feedback = "wrong"
                        update_streak(is_correct)
                        rerun_app()
                with col_opt_spk:
                    render_speaker_button(opt, f"quiz_opt_{question_idx}_{i}")
    else:
        st.markdown("### 📋 Hasil Jawaban")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**📖 Soal**")
            st.info(st.session_state.current_soal)
            if st.session_state.current_pinyin:
                st.markdown(f"**Pinyin soal**  \n`{st.session_state.current_pinyin}`")
            st.markdown("**Jawaban Anda**")
            user_ans = st.session_state.user_answer if hasattr(st.session_state, 'user_answer') else "-"
            if st.session_state.quiz_feedback == "correct":
                color = "green"
            else:
                color = "red"
            st.markdown(f"<span style='color:{color}'>{user_ans}</span>", unsafe_allow_html=True)
            if st.session_state.quiz_mode == "Arti → Hanzi" and user_ans != "-":
                user_row = vocab[vocab["Kosakata"] == user_ans]
                if not user_row.empty:
                    st.markdown(f"**Pinyin jawaban Anda**  \n`{user_row.iloc[0]['Pinyin']}`")
                    st.markdown(f"**Arti jawaban Anda**  \n{user_row.iloc[0]['Arti Indonesia']}")
        with col2:
            st.markdown("**✅ Jawaban Benar**")
            st.success(st.session_state.current_benar)
            if st.session_state.quiz_mode == "Hanzi → Arti":
                st.markdown(f"**Arti jawaban**  \n{st.session_state.current_benar}")
            else:
                pinyin_benar = st.session_state.current_item.get("Pinyin", "")
                if pinyin_benar:
                    st.markdown(f"**Pinyin jawaban**  \n`{pinyin_benar}`")
                st.markdown(f"**Arti jawaban**  \n{st.session_state.current_item.get('Arti Indonesia', '')}")
        if st.session_state.quiz_feedback == "correct":
            st.success("✅ Benar! +10 poin")
        else:
            st.error("❌ Salah. Pelajari lagi kosakatanya.")
        if st.button("➡️ Soal berikutnya", type="primary", use_container_width=True):
            st.session_state.quiz_idx = (idx + 1) % len(pool)
            st.session_state.quiz_options = []
            st.session_state.quiz_answered = False
            st.session_state.quiz_feedback = None
            if 'user_answer' in st.session_state:
                del st.session_state.user_answer
            rerun_app()
    st.metric("Skor Kuis", st.session_state.score_quiz)

def cloze_view():
    st.markdown("<div class='glass-card'><h2>✏️ Isi Kalimat Kosong</h2><p>Isi titik-titik dengan pilihan yang tepat.</p></div>", unsafe_allow_html=True)
    render_top_dashboard()
    if cloze is None or len(cloze)==0:
        st.warning("Belum ada soal.")
        return
    total = len(cloze)
    pool = build_quiz_pool(total, st.session_state.wrong_cloze)
    if not pool: return
    idx = st.session_state.clz_idx % len(pool)
    question_idx = pool[idx]
    soal = cloze.iloc[question_idx]
    if not st.session_state.clz_options:
        pilihan = [soal["pilihan1"], soal["pilihan2"], soal["pilihan3"], soal["pilihan4"]]
        pilihan = [opt for opt in pilihan if opt]
        random.shuffle(pilihan)
        st.session_state.clz_options = pilihan
        st.session_state.clz_answered = False
        st.session_state.clz_feedback = None
        st.session_state.current_kalimat = soal["kalimat"]
        st.session_state.current_benar_cloze = soal["jawaban_benar"]
        st.session_state.pinyin_kal = soal.get("pinyin","")
        st.session_state.current_alasan = soal.get("alasan","")
    st.progress((idx+1)/len(pool))
    st.caption(f"Soal {idx+1} dari {len(pool)}")
    col_kal, col_spk = st.columns([4,1])
    with col_kal:
        st.markdown(f"<div class='glass-card'>{st.session_state.current_kalimat}</div>", unsafe_allow_html=True)
    with col_spk:
        render_speaker_button(st.session_state.current_kalimat, f"cloze_soal_{question_idx}")
    if st.button("🔊 Tampilkan Pinyin Kalimat", key="clz_pin"):
        st.session_state.clz_show_pinyin = not st.session_state.clz_show_pinyin
        rerun_app()
    if st.session_state.clz_show_pinyin and st.session_state.pinyin_kal:
        st.caption(f"Pinyin: {st.session_state.pinyin_kal}")
    if not st.session_state.clz_answered:
        cols = st.columns(2)
        for i, opt in enumerate(st.session_state.clz_options):
            with cols[i%2]:
                col_btn, col_opt_spk = st.columns([4,1])
                with col_btn:
                    if st.button(opt, key=f"clz_{question_idx}_{i}", use_container_width=True):
                        st.session_state.clz_answered = True
                        st.session_state.cloze_attempts += 1
                        is_correct = opt == st.session_state.current_benar_cloze
                        st.session_state.user_answer = opt
                        if is_correct:
                            st.session_state.cloze_correct_attempts += 1
                            if question_idx not in st.session_state.cloze_answered_set:
                                st.session_state.score_cloze += 10
                                st.session_state.cloze_answered_set.add(question_idx)
                            st.session_state.wrong_cloze.discard(question_idx)
                            st.session_state.clz_feedback = "correct"
                        else:
                            st.session_state.wrong_cloze.add(question_idx)
                            st.session_state.clz_feedback = "wrong"
                        update_streak(is_correct)
                        rerun_app()
                with col_opt_spk:
                    render_speaker_button(opt, f"cloze_opt_{question_idx}_{i}")
    else:
        st.markdown("### 📋 Hasil Jawaban")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**📝 Kalimat soal**")
            st.info(st.session_state.current_kalimat)
            st.markdown("**Jawaban Anda**")
            user_ans = st.session_state.user_answer if hasattr(st.session_state, 'user_answer') else "-"
            if st.session_state.clz_feedback == "correct":
                color = "green"
            else:
                color = "red"
            st.markdown(f"<span style='color:{color}'>{user_ans}</span>", unsafe_allow_html=True)
        with col2:
            st.markdown("**✅ Jawaban Benar**")
            st.success(st.session_state.current_benar_cloze)
            if st.session_state.current_alasan:
                st.markdown(f"**📖 Penjelasan**  \n{st.session_state.current_alasan}")
        if st.session_state.clz_feedback == "correct":
            st.success("✅ Tepat! +10 poin")
        else:
            st.error("❌ Salah. Perhatikan konteks kalimat.")
        if st.button("📌 Soal berikutnya", use_container_width=True):
            st.session_state.clz_idx = (idx+1) % len(pool)
            st.session_state.clz_options = []
            st.session_state.clz_answered = False
            st.session_state.clz_feedback = None
            if 'user_answer' in st.session_state:
                del st.session_state.user_answer
            rerun_app()
    st.metric("Skor Isi Kalimat", st.session_state.score_cloze)

def scramble_view():
    st.markdown("<div class='glass-card'><h2>🔄 Susun Kalimat Acak</h2><p>Susun kata-kata menjadi kalimat yang benar.</p></div>", unsafe_allow_html=True)
    render_top_dashboard()
    if scramble is None or len(scramble)==0:
        st.warning("Belum ada soal.")
        return
    total = len(scramble)
    pool = build_quiz_pool(total, st.session_state.wrong_scramble)
    if not pool: return
    idx = st.session_state.sc_idx % len(pool)
    question_idx = pool[idx]
    original_text = str(scramble.iloc[question_idx].get("kalimat_asli",""))
    if st.session_state.sc_idx != idx or not st.session_state.sc_original:
        tokens = [t for t in jieba.cut(original_text) if t.strip()]
        st.session_state.sc_original = tokens
        st.session_state.sc_tokens = deepcopy(tokens)
        random.shuffle(st.session_state.sc_tokens)
        st.session_state.sc_order = []
        st.session_state.sc_answered = False
        st.session_state.sc_feedback = None
        st.session_state.current_pola = scramble.iloc[question_idx].get("pola","")
    st.progress((idx+1)/len(pool))
    st.caption(f"Soal {idx+1} dari {len(pool)}")
    col_info, col_spk = st.columns([4,1])
    with col_info:
        st.markdown("**🔀 Susun kata-kata menjadi kalimat yang benar:**")
    with col_spk:
        render_speaker_button(original_text, f"scramble_soal_{question_idx}")
    if not st.session_state.sc_answered:
        if st.session_state.sc_tokens:
            cols = st.columns(min(4, len(st.session_state.sc_tokens)))
            for i, tok in enumerate(st.session_state.sc_tokens):
                with cols[i%len(cols)]:
                    col_tok, col_tok_spk = st.columns([4,1])
                    with col_tok:
                        if st.button(tok, key=f"sc_{question_idx}_{i}_{tok}", use_container_width=True):
                            st.session_state.sc_order.append(tok)
                            st.session_state.sc_tokens.pop(i)
                            rerun_app()
                    with col_tok_spk:
                        render_speaker_button(tok, f"sc_tok_{question_idx}_{i}")
        else:
            st.info("✅ Semua kata sudah dipilih. Klik 'Cek Jawaban'.")
        if st.session_state.sc_order:
            st.markdown("**📝 Urutan Anda:** " + " ".join(st.session_state.sc_order))
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("🔄 Reset", use_container_width=True):
                st.session_state.sc_tokens = deepcopy(st.session_state.sc_original)
                random.shuffle(st.session_state.sc_tokens)
                st.session_state.sc_order = []
                rerun_app()
        with col_b:
            if st.button("✅ Cek Jawaban", use_container_width=True):
                st.session_state.sc_answered = True
                st.session_state.scramble_attempts += 1
                joined_answer = "".join(st.session_state.sc_order).replace(" ","")
                joined_original = "".join(st.session_state.sc_original).replace(" ","")
                is_correct = joined_answer == joined_original
                st.session_state.user_answer = " ".join(st.session_state.sc_order) if st.session_state.sc_order else "(kosong)"
                if is_correct:
                    st.session_state.scramble_correct_attempts += 1
                    st.session_state.sc_feedback = "correct"
                    if question_idx not in st.session_state.scramble_scored_set:
                        st.session_state.score_scramble += 10
                        st.session_state.scramble_scored_set.add(question_idx)
                    st.session_state.wrong_scramble.discard(question_idx)
                else:
                    st.session_state.sc_feedback = "wrong"
                    st.session_state.wrong_scramble.add(question_idx)
                update_streak(is_correct)
                rerun_app()
    else:
        st.markdown("### 📋 Hasil Jawaban")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**📝 Kalimat asli (soal)**")
            st.info(' '.join(st.session_state.sc_original))
            st.markdown("**Urutan Anda**")
            user_ans = st.session_state.user_answer if hasattr(st.session_state, 'user_answer') else "-"
            if st.session_state.sc_feedback == "correct":
                color = "green"
            else:
                color = "red"
            st.markdown(f"<span style='color:{color}'>{user_ans}</span>", unsafe_allow_html=True)
        with col2:
            st.markdown("**✅ Urutan Benar**")
            st.success(' '.join(st.session_state.sc_original))
            if st.session_state.current_pola:
                st.markdown(f"**📖 Pola grammar**  \n{st.session_state.current_pola}")
        if st.session_state.sc_feedback == "correct":
            st.success("✅ Kalimat benar! +10 poin")
        else:
            st.error("❌ Urutan salah. Perhatikan pola kalimat.")
        col_next, col_tryagain = st.columns(2)
        with col_next:
            if st.button("➡️ Soal berikutnya", type="primary", use_container_width=True):
                st.session_state.sc_idx = (idx+1) % len(pool)
                st.session_state.sc_tokens = []
                st.session_state.sc_original = []
                st.session_state.sc_order = []
                st.session_state.sc_answered = False
                st.session_state.sc_feedback = None
                if 'user_answer' in st.session_state:
                    del st.session_state.user_answer
                rerun_app()
        with col_tryagain:
            if st.button("🔄 Coba lagi soal ini", use_container_width=True):
                st.session_state.sc_tokens = deepcopy(st.session_state.sc_original)
                random.shuffle(st.session_state.sc_tokens)
                st.session_state.sc_order = []
                st.session_state.sc_answered = False
                st.session_state.sc_feedback = None
                rerun_app()
    st.metric("Skor Susun Kalimat", st.session_state.score_scramble)


# ==================== LOAD DATA H31003 ====================
@st.cache_data
def load_h31003_data():
    """Memuat semua sheet dari file h31003.xlsx"""
    try:
        h31003_file = os.path.join(APP_DIR, "h31003.xlsx")
        if not os.path.exists(h31003_file):
            return None
        df_match = pd.read_excel(h31003_file, sheet_name="H31003_reading_41_50")
        df_fillword = pd.read_excel(h31003_file, sheet_name="H31003_reading_51_60")
        df_mc = pd.read_excel(h31003_file, sheet_name="H31003_reading_61_70")
        df_char = pd.read_excel(h31003_file, sheet_name="H31003_writing_71_75")
        df_scramble = pd.read_excel(h31003_file, sheet_name="H31003_writing_76_80")
        df_listening = pd.read_excel(h31003_file, sheet_name="H31003_listening_1_10")
        return df_match, df_fillword, df_mc, df_char, df_scramble, df_listening
    except Exception as e:
        st.error(f"Gagal memuat data H31003: {e}")
        return None

# ==================== LATIHAN SOAL H31003 ====================
def h31003_exam():
    st.markdown("<div class='glass-card'><h2>📝 Latihan Soal HSK 3 (H31003)</h2><p>Kerjakan semua soal secara berurutan. Setiap halaman berisi 5 soal. Skor akan dihitung setelah selesai.</p></div>", unsafe_allow_html=True)

    data = load_h31003_data()
    if data is None:
        st.warning("File h31003.xlsx tidak ditemukan. Pastikan file ada di folder yang sama.")
        return

    df_match, df_fillword, df_mc, df_char, df_scramble, df_listening = data

    # ========== Membangun daftar semua soal ==========
    all_questions = []

    # LISTENING
    for _, row in df_listening.iterrows():
        all_questions.append({
            "type": "listening",
            "id": row['no'],
            "part": 1,
            "audio_text": row['dialog'],
            "options": ['A', 'B', 'C', 'E', 'F'],
            "correct": str(row['correct']).strip().upper(),
            "image_path": str(row.get('image_path', '')).strip(),
        })

    # MATCHING (41-50)
    for _, row in df_match.iterrows():
        all_questions.append({
            "type": "matching",
            "soal": str(row.get("soal", "")),
            "jawaban_benar": str(row.get("jawaban", "")),
            "arti_soal": str(row.get("arti1", "")),
            "pinyin_soal": str(row.get("pinyin1", "")),
            "arti_jawaban": str(row.get("arti2", "")),
            "pinyin_jawaban": str(row.get("pinyin2", "")),
        })

    # FILLWORD (51-60)
    for _, row in df_fillword.iterrows():
        all_questions.append({
            "type": "fillword",
            "soal": str(row.get("soal", "")),
            "jawaban_benar": str(row.get("jawaban", "")),
            "arti_soal": str(row.get("arti", "")),
            "pinyin_soal": str(row.get("pinyin1", "")),
        })

    # PILIHAN GANDA (61-70)
    for _, row in df_mc.iterrows():
        all_questions.append({
            "type": "mc",
            "soal": str(row.get("soal", "")),
            "jawaban_benar": str(row.get("jawaban", "")),
            "opsi_A": str(row.get("opsi_A", "")),
            "opsi_B": str(row.get("opsi_B", "")),
            "opsi_C": str(row.get("opsi_C", "")),
            "pinyin_soal": str(row.get("pinyin_soal", "")),
            "arti_soal": str(row.get("arti_soal", "")),
            "pilihan": {
                "A": {"teks": str(row.get("opsi_A", "")), "pinyin": str(row.get("pinyin_A", "")), "arti": str(row.get("arti_A", ""))},
                "B": {"teks": str(row.get("opsi_B", "")), "pinyin": str(row.get("pinyin_B", "")), "arti": str(row.get("arti_B", ""))},
                "C": {"teks": str(row.get("opsi_C", "")), "pinyin": str(row.get("pinyin_C", "")), "arti": str(row.get("arti_C", ""))},
            }
        })

    # ISIAN HURUF (71-75)
    for _, row in df_char.iterrows():
        all_questions.append({
            "type": "char",
            "soal": str(row.get("soal", "")),
            "jawaban_benar": str(row.get("jawaban", "")),
            "arti_soal": str(row.get("arti", "")),
            "pinyin_soal": str(row.get("pinyin", "")),
        })

    # SUSUN KALIMAT (76-80)
    for _, row in df_scramble.iterrows():
        kalimat = str(row.get("soal", ""))
        tokens = [t for t in jieba.cut(kalimat) if t.strip()]
        all_questions.append({
            "type": "scramble",
            "soal": kalimat,
            "soal_asli": kalimat,
            "tokens": tokens,
            "jawaban_benar": "".join(tokens).replace(" ", ""),
            "arti_soal": str(row.get("arti", "")),
            "pinyin_soal": str(row.get("pinyin", "")),
        })

    total_soal = len(all_questions)
    per_page = 5
    total_pages = (total_soal - 1) // per_page + 1

    # ========== INISIALISASI SESSION STATE ==========
    if 'h31003_answers' not in st.session_state:
        st.session_state.h31003_answers = [None] * total_soal
    else:
        if len(st.session_state.h31003_answers) != total_soal:
            st.session_state.h31003_answers = [None] * total_soal

    if 'h31003_page' not in st.session_state:
        st.session_state.h31003_page = 0
    if 'h31003_reviewed' not in st.session_state:
        st.session_state.h31003_reviewed = [False] * total_pages
    if 'h31003_finished' not in st.session_state:
        st.session_state.h31003_finished = False
    if 'h31003_score' not in st.session_state:
        st.session_state.h31003_score = 0
    if 'h31003_match_shuffle' not in st.session_state:
        st.session_state.h31003_match_shuffle = {}

    # ========== TOMBOL RESET ==========
    if st.button("🔄 Reset Latihan H31003", use_container_width=True):
        for key in list(st.session_state.keys()):
            if (key.startswith("h31003_") or
                key.startswith("scramble_tokens_") or
                key.startswith("scramble_order_") or
                key.startswith("show_pinyin_h31003_") or
                key.startswith("match_shuffle_") or
                key.startswith("fillword_options_")):
                st.session_state.pop(key, None)
        st.rerun()

    current_page = st.session_state.h31003_page
    if current_page >= total_pages:
        st.session_state.h31003_finished = True

    # ========== SELESAI (FINISH) ==========
    if st.session_state.h31003_finished:
        correct = 0
        for i, ans in enumerate(st.session_state.h31003_answers):
            if ans is not None and ans == all_questions[i]["jawaban_benar"]:
                correct += 1
        st.session_state.h31003_score = correct
        st.balloons()
        st.success(f"✨ Latihan selesai! Skor Anda: {correct} dari {total_soal} ({correct/total_soal*100:.1f}%)")
        if st.button("Kerjakan Ulang", use_container_width=True):
            for key in list(st.session_state.keys()):
                if (key.startswith("h31003_") or
                    key.startswith("scramble_tokens_") or
                    key.startswith("scramble_order_") or
                    key.startswith("show_pinyin_h31003_") or
                    key.startswith("match_shuffle_") or
                    key.startswith("fillword_options_")):
                    st.session_state.pop(key, None)
            st.rerun()
        return

    # ========== TENTUKAN HALAMAN SAAT INI ==========
    start = current_page * per_page
    end = min(start + per_page, total_soal)
    page_soal = all_questions[start:end]

    st.markdown(f"### Halaman {current_page+1} dari {total_pages}")
    st.progress((current_page) / total_pages)

    # ========== TAMPILKAN GAMBAR LISTENING (jika ada) ==========
    listening_items = []
    for q in page_soal:
        if q["type"] == "listening" and q.get("image_path") and os.path.exists(q["image_path"]):
            listening_items.append({
                "image_path": q["image_path"],
                "options": q.get("options", ['A', 'B', 'C', 'E', 'F'])
            })

    if listening_items:
        st.markdown("### 🖼️ Gambar untuk Soal Listening")
        cols = st.columns(min(len(listening_items), 5))
        for i, item in enumerate(listening_items):
            with cols[i % 5]:
                st.image(item["image_path"], use_container_width=True)
                # Hanya tampilkan satu huruf dari nama file (opsional)
                fname = os.path.basename(item["image_path"])
                match = re.search(r'_([A-F])\.(jpg|png|jpeg|webp)$', fname, re.IGNORECASE)
                label_huruf = match.group(1) if match else "?"
                st.markdown(f"<div style='text-align:center; font-size:0.9rem; margin-top:5px;'><strong>{label_huruf}</strong></div>", unsafe_allow_html=True)
        st.markdown("---")

    # ========== PERSIAPAN DATA UNTUK FILLWORD & MATCHING ==========
    all_fill_words = list(set([q["jawaban_benar"] for q in all_questions if q["type"] == "fillword"]))
    if not all_fill_words and any(q["type"] == "fillword" for q in page_soal):
        st.error("Data untuk soal fillword (51-60) kosong. Periksa file h31003.xlsx.")
        return

    match_answers_in_page = [q["jawaban_benar"] for q in page_soal if q["type"] == "matching"]
    if match_answers_in_page:
        shuffle_key = f"match_shuffle_{current_page}"
        if shuffle_key not in st.session_state.h31003_match_shuffle:
            shuffled = match_answers_in_page.copy()
            random.shuffle(shuffled)
            st.session_state.h31003_match_shuffle[shuffle_key] = shuffled
        shuffled_match_answers = st.session_state.h31003_match_shuffle[shuffle_key]
    else:
        shuffled_match_answers = []

    # ========== TAMPILKAN SOAL ATAU REVIEW ==========
    if not st.session_state.h31003_reviewed[current_page]:
        # ========== LOOP SOAL ==========
        for idx, q in enumerate(page_soal):
            global_idx = start + idx
            with st.container():
                if q["type"] == "listening":
                    st.markdown(f"**Soal {global_idx+1}** (Bagian {q['part']})")
                    if st.button(f"🔊 Dengarkan Soal {global_idx+1}", key=f"listen_audio_{global_idx}"):
                        audio_bytes = get_audio_bytes(q['audio_text'], lang='zh')
                        if audio_bytes:
                            st.audio(audio_bytes, format="audio/mp3", autoplay=True)
                        else:
                            st.warning("Gagal memutar audio.")
                    current_ans = st.session_state.h31003_answers[global_idx]
                    options = q['options']
                    if current_ans is None:
                        default_idx = 0
                    else:
                        try:
                            default_idx = options.index(current_ans)
                        except ValueError:
                            default_idx = 0
                    selected = st.selectbox(
                        "Pilih jawaban",
                        options,
                        index=default_idx,
                        key=f"listening_dropdown_{global_idx}",
                        label_visibility="collapsed"
                    )
                    st.session_state.h31003_answers[global_idx] = selected
                    st.divider()

                elif q["type"] == "matching":
                    col_q, col_spk = st.columns([4, 1])
                    with col_q:
                        st.markdown(f"**Soal {global_idx+1}.** {q['soal']}")
                    with col_spk:
                        render_speaker_button(q['soal'], f"h31003_soal_{global_idx}")
                    pinyin_key = f"show_pinyin_h31003_{global_idx}"
                    if pinyin_key not in st.session_state:
                        st.session_state[pinyin_key] = False
                    if st.button("🔊 Lihat Pinyin", key=f"pinyin_btn_{global_idx}"):
                        st.session_state[pinyin_key] = not st.session_state[pinyin_key]
                        st.rerun()
                    if st.session_state[pinyin_key] and q.get("pinyin_soal"):
                        st.caption(f"Pinyin: {q['pinyin_soal']}")
                    current_ans = st.session_state.h31003_answers[global_idx]
                    default_idx = shuffled_match_answers.index(current_ans) if current_ans in shuffled_match_answers else 0
                    st.session_state.h31003_answers[global_idx] = st.selectbox(
                        f"Pilih jawaban untuk soal {global_idx+1}",
                        shuffled_match_answers,
                        index=default_idx,
                        key=f"h31003_match_{global_idx}",
                        label_visibility="collapsed"
                    )
                    st.divider()

                elif q["type"] == "fillword":
                    st.markdown(f"**Soal {global_idx+1}.** {q['soal']}")
                    correct_ans = q["jawaban_benar"]
                    other_words = [w for w in all_fill_words if w != correct_ans]
                    if len(other_words) >= 4:
                        distractor = random.sample(other_words, 4)
                    else:
                        distractor = other_words + ["(Tidak ada)"] * (4 - len(other_words))
                    pilihan_fill = [correct_ans] + distractor
                    random.shuffle(pilihan_fill)
                    fill_key = f"fillword_options_{global_idx}"
                    if fill_key not in st.session_state:
                        st.session_state[fill_key] = pilihan_fill
                    current_ans = st.session_state.h31003_answers[global_idx]
                    default_idx = st.session_state[fill_key].index(current_ans) if current_ans in st.session_state[fill_key] else 0
                    st.session_state.h31003_answers[global_idx] = st.selectbox(
                        f"Pilih kata yang tepat untuk soal {global_idx+1}",
                        st.session_state[fill_key],
                        index=default_idx,
                        key=f"h31003_fillword_{global_idx}",
                        label_visibility="collapsed"
                    )
                    st.divider()

                elif q["type"] == "mc":
                    st.markdown(f"**Soal {global_idx+1}.** {q['soal']}")
                    pilihan_teks = [q["opsi_A"], q["opsi_B"], q["opsi_C"]]
                    current_ans = st.session_state.h31003_answers[global_idx]
                    default_idx = pilihan_teks.index(current_ans) if current_ans in pilihan_teks else 0
                    st.session_state.h31003_answers[global_idx] = st.radio(
                        f"Pilih jawaban untuk soal {global_idx+1}",
                        pilihan_teks,
                        index=default_idx,
                        key=f"h31003_mc_{global_idx}",
                        label_visibility="collapsed"
                    )
                    st.divider()

                elif q["type"] == "char":
                    st.markdown(f"**Soal {global_idx+1}.** {q['soal']}")
                    current_ans = st.session_state.h31003_answers[global_idx] or ""
                    st.session_state.h31003_answers[global_idx] = st.text_input(
                        f"Masukkan satu huruf (Hanzi) untuk soal {global_idx+1}",
                        value=current_ans,
                        key=f"h31003_char_{global_idx}",
                        label_visibility="collapsed"
                    )
                    st.divider()

                elif q["type"] == "scramble":
                    token_key = f"scramble_tokens_{global_idx}"
                    order_key = f"scramble_order_{global_idx}"
                    if token_key not in st.session_state:
                        st.session_state[token_key] = deepcopy(q["tokens"])
                        random.shuffle(st.session_state[token_key])
                        st.session_state[order_key] = []
                    st.markdown(f"**Soal {global_idx+1}. Susun kalimat:**")
                    st.markdown("🔀 **Klik kata-kata di bawah untuk menyusun kalimat yang benar.**")
                    if st.session_state[token_key]:
                        cols = st.columns(min(4, len(st.session_state[token_key])))
                        for j, tok in enumerate(st.session_state[token_key]):
                            with cols[j % len(cols)]:
                                col_tok, col_tok_spk = st.columns([4, 1])
                                with col_tok:
                                    if st.button(tok, key=f"scramble_btn_{global_idx}_{j}"):
                                        st.session_state[order_key].append(tok)
                                        st.session_state[token_key].pop(j)
                                        st.rerun()
                                with col_tok_spk:
                                    render_speaker_button(tok, f"scramble_tok_{global_idx}_{j}")
                    else:
                        st.info("✅ Semua kata sudah dipilih.")
                    if st.session_state[order_key]:
                        st.markdown("**📝 Urutan Anda:** " + " ".join(st.session_state[order_key]))
                    col_reset, col_cek = st.columns(2)
                    with col_reset:
                        if st.button("🔄 Reset", key=f"reset_scramble_{global_idx}"):
                            st.session_state[token_key] = deepcopy(q["tokens"])
                            random.shuffle(st.session_state[token_key])
                            st.session_state[order_key] = []
                            st.rerun()
                    with col_cek:
                        if st.button("✅ Cek Jawaban", key=f"check_scramble_{global_idx}"):
                            user_answer = "".join(st.session_state[order_key]).replace(" ", "")
                            correct_answer = q["jawaban_benar"]
                            is_correct = (user_answer == correct_answer)
                            st.session_state.h31003_answers[global_idx] = user_answer if is_correct else None
                            st.session_state[f"scramble_feedback_{global_idx}"] = is_correct
                            st.rerun()
                    feedback_key = f"scramble_feedback_{global_idx}"
                    if feedback_key in st.session_state:
                        if st.session_state[feedback_key]:
                            st.success("✅ Susunan benar!")
                        else:
                            st.error(f"❌ Susunan salah. Kalimat yang benar: {q['soal_asli']}")
                    st.divider()

                else:
                    st.markdown(f"**Soal {global_idx+1}.** {q.get('soal', 'Soal tidak dikenal')}")
                    st.divider()

        if st.button("✅ Cek Jawaban (Halaman Ini)", key=f"check_{current_page}", use_container_width=True):
            st.session_state.h31003_reviewed[current_page] = True
            st.rerun()

    else:
        # ========== REVIEW MODE ==========
        st.subheader("📋 Review Jawaban Halaman Ini")
        for idx, q in enumerate(page_soal):
            global_idx = start + idx
            user_ans = st.session_state.h31003_answers[global_idx]
            correct_ans = q.get("jawaban_benar", q.get("correct"))
            is_correct = (user_ans == correct_ans)

            if q["type"] == "listening":
                st.markdown(f"**{global_idx+1}. (Listening)** {'✅' if is_correct else '❌'}")
                if q.get("image_path") and os.path.exists(q["image_path"]):
                    st.image(q["image_path"], width=200)
                st.markdown(f"- Jawaban Anda: `{user_ans}`")
                st.markdown(f"- Jawaban benar: `{correct_ans}`")
            elif q["type"] == "matching":
                st.markdown(f"**{global_idx+1}. {q['soal']}** {'✅' if is_correct else '❌'}")
                st.markdown(f"- Jawaban Anda: `{user_ans}`")
                st.markdown(f"- Jawaban benar: `{correct_ans}`")
                if q.get("arti_jawaban"):
                    st.markdown(f"- Arti jawaban: {q['arti_jawaban']}")
                if q.get("arti_soal"):
                    st.markdown(f"- Arti soal: {q['arti_soal']}")
            elif q["type"] == "fillword":
                st.markdown(f"**{global_idx+1}. {q['soal']}** {'✅' if is_correct else '❌'}")
                st.markdown(f"- Jawaban Anda: `{user_ans}`")
                st.markdown(f"- Jawaban benar: `{correct_ans}`")
            elif q["type"] == "mc":
                st.markdown(f"**{global_idx+1}. {q['soal']}** {'✅' if is_correct else '❌'}")
                st.markdown(f"- Jawaban Anda: `{user_ans}`")
                st.markdown(f"- Jawaban benar: `{correct_ans}`")
                for opt in ["A", "B", "C"]:
                    if q["pilihan"][opt]["teks"] == correct_ans:
                        if q["pilihan"][opt]["pinyin"]:
                            st.markdown(f"  - Pinyin: `{q['pilihan'][opt]['pinyin']}`")
                        if q["pilihan"][opt]["arti"]:
                            st.markdown(f"  - Arti: {q['pilihan'][opt]['arti']}")
                        break
            elif q["type"] == "char":
                st.markdown(f"**{global_idx+1}. {q['soal']}** {'✅' if is_correct else '❌'}")
                st.markdown(f"- Jawaban Anda: `{user_ans}`")
                st.markdown(f"- Jawaban benar: `{correct_ans}`")
            elif q["type"] == "scramble":
                st.markdown(f"**{global_idx+1}. Susun kalimat** {'✅' if is_correct else '❌'}")
                user_display = user_ans if user_ans else "(belum selesai)"
                st.markdown(f"- Jawaban Anda: `{user_display}`")
                st.markdown(f"- Kalimat benar: `{q['soal_asli']}`")
                if q.get("arti_soal"):
                    st.markdown(f"- Arti: {q['arti_soal']}")

            st.markdown("---")

        if st.button("➡️ Lanjut ke Halaman Berikutnya", key=f"next_{current_page}", use_container_width=True):
            if current_page + 1 < total_pages:
                st.session_state.h31003_page = current_page + 1
                st.session_state.h31003_reviewed[current_page + 1] = False
                st.rerun()
            else:
                st.session_state.h31003_finished = True
                st.rerun()
# ==================== ROUTER ====================
if not profile_is_complete():
    render_profile_setup()
    st.stop()

if st.session_state.menu == "📇 Flashcard":
    flashcard_view()
elif st.session_state.menu == "📝 Kuis Kosakata":
    kuis_view()
elif st.session_state.menu == "✏️ Isi Kalimat":
    cloze_view()
elif st.session_state.menu == "🔄 Susun Kalimat":
    scramble_view()
elif st.session_state.menu == "H31003 Exam":
    h31003_exam()
else:
    scramble_view()

save_progress()
