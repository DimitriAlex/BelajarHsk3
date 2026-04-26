import json
import os
import random
from copy import deepcopy

import jieba
import pandas as pd
import streamlit as st

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

@st.cache_data
def load_matching_data():
    try:
        matching_df = pd.read_excel(DATA_FILE, sheet_name="susun_jawaban1")
        return matching_df.fillna("")
    except Exception:
        return None

matching_df = load_matching_data()

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
    if st.button("📝 Susun Jawaban", key="menu_match", use_container_width=True):
        st.session_state.menu = "Susun Jawaban"
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
    st.progress((idx+1)/len(pool))
    st.caption(f"Soal {idx+1} dari {len(pool)} | Streak {st.session_state.current_streak}")
    st.markdown(f"<div class='hanzi-giant'>{st.session_state.current_soal}</div>", unsafe_allow_html=True)
    if st.button("🔊 Tampilkan Pinyin", key="quiz_pin"):
        st.session_state.quiz_show_pinyin = not st.session_state.quiz_show_pinyin
        rerun_app()
    if st.session_state.quiz_show_pinyin:
        st.markdown(f"<div style='text-align:center'><span class='pinyin-chip'>{st.session_state.current_pinyin}</span></div>", unsafe_allow_html=True)
    if not st.session_state.quiz_answered:
        cols = st.columns(2)
        for i, opt in enumerate(st.session_state.quiz_options):
            with cols[i%2]:
                if st.button(opt, key=f"quiz_{question_idx}_{i}", use_container_width=True):
                    st.session_state.quiz_answered = True
                    st.session_state.quiz_attempts += 1
                    is_correct = opt == st.session_state.current_benar
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
    else:
        if st.session_state.quiz_feedback == "correct":
            st.success("Benar.")
        else:
            st.error(f"Salah. Jawaban benar: {st.session_state.current_benar}")
            st.markdown(f"<div class='hint-box'><strong>Pinyin:</strong> {st.session_state.current_pinyin}<br><strong>Arti:</strong> {st.session_state.current_arti}<br><strong>Contoh:</strong> {st.session_state.current_contoh or '-'}</div>", unsafe_allow_html=True)
        if st.button("➡️ Soal berikutnya", type="primary", use_container_width=True):
            st.session_state.quiz_idx = (idx + 1) % len(pool)
            st.session_state.quiz_options = []
            st.session_state.quiz_answered = False
            st.session_state.quiz_feedback = None
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
    st.markdown(f"<div class='glass-card'>{st.session_state.current_kalimat}</div>", unsafe_allow_html=True)
    if st.button("🔊 Tampilkan Pinyin Kalimat", key="clz_pin"):
        st.session_state.clz_show_pinyin = not st.session_state.clz_show_pinyin
        rerun_app()
    if st.session_state.clz_show_pinyin and st.session_state.pinyin_kal:
        st.caption(f"Pinyin: {st.session_state.pinyin_kal}")
    if not st.session_state.clz_answered:
        cols = st.columns(2)
        for i, opt in enumerate(st.session_state.clz_options):
            with cols[i%2]:
                if st.button(opt, key=f"clz_{question_idx}_{i}", use_container_width=True):
                    st.session_state.clz_answered = True
                    st.session_state.cloze_attempts += 1
                    is_correct = opt == st.session_state.current_benar_cloze
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
    else:
        if st.session_state.clz_feedback == "correct":
            st.success("Tepat!")
        else:
            st.error(f"Jawaban benar: {st.session_state.current_benar_cloze}")
            if st.session_state.current_alasan:
                st.info(f"📖 Penjelasan: {st.session_state.current_alasan}")
        if st.button("📌 Soal berikutnya", use_container_width=True):
            st.session_state.clz_idx = (idx+1) % len(pool)
            st.session_state.clz_options = []
            st.session_state.clz_answered = False
            st.session_state.clz_feedback = None
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
    st.markdown("**Susun kata-kata di bawah menjadi kalimat yang benar**")
    if not st.session_state.sc_answered:
        if st.session_state.sc_tokens:
            cols = st.columns(min(4, len(st.session_state.sc_tokens)))
            for i, tok in enumerate(st.session_state.sc_tokens):
                with cols[i%len(cols)]:
                    if st.button(tok, key=f"sc_{question_idx}_{i}_{tok}", use_container_width=True):
                        st.session_state.sc_order.append(tok)
                        st.session_state.sc_tokens.pop(i)
                        rerun_app()
        else:
            st.info("Semua kata sudah dipilih. Klik 'Cek Jawaban'.")
        if st.session_state.sc_order:
            st.markdown("**Urutan Anda:** " + " ".join(st.session_state.sc_order))
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
        if st.session_state.sc_feedback == "correct":
            st.success("Kalimat benar.")
        else:
            st.error(f"Urutan yang benar: {' '.join(st.session_state.sc_original)}")
            if st.session_state.current_pola:
                st.info(f"📖 Pola grammar: {st.session_state.current_pola}")
        col_next, col_tryagain = st.columns(2)
        with col_next:
            if st.button("➡️ Soal berikutnya", type="primary", use_container_width=True):
                st.session_state.sc_idx = (idx+1) % len(pool)
                st.session_state.sc_tokens = []
                st.session_state.sc_original = []
                st.session_state.sc_order = []
                st.session_state.sc_answered = False
                st.session_state.sc_feedback = None
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

def matching_view():
    st.markdown(
        "<div class='glass-card'><h2 style='margin:0'>📝 Susun Jawaban</h2><p style='margin-bottom:0'>Pasangkan soal dengan jawaban yang tepat. Klik tombol pinyin untuk melihat bacaan.</p></div>",
        unsafe_allow_html=True,
    )
    render_top_dashboard()

    if matching_df is None or matching_df.empty:
        st.warning("Data 'susun_jawaban1' tidak ditemukan. Periksa file Excel.")
        return

    kode_list = matching_df["kode"].unique()
    selected_kode = st.radio("Pilih paket soal", kode_list, horizontal=True)

    # Filter data berdasarkan kode
    data = matching_df[matching_df["kode"] == selected_kode].copy()
    if len(data) == 0:
        st.warning(f"Tidak ada data untuk kode {selected_kode}")
        return

    key_prefix = f"matching_{selected_kode}"

    # Reset state jika ganti kode
    if "last_matching_kode" not in st.session_state:
        st.session_state.last_matching_kode = selected_kode
    if st.session_state.last_matching_kode != selected_kode:
        for k in list(st.session_state.keys()):
            if k.startswith("matching_") or k.startswith("match_") or k.startswith("show_pinyin_"):
                st.session_state.pop(k, None)
        st.session_state.last_matching_kode = selected_kode

    # Inisialisasi state
    if f"{key_prefix}_answers" not in st.session_state:
        st.session_state[f"{key_prefix}_answers"] = [None] * len(data)
        st.session_state[f"{key_prefix}_submitted"] = False
        st.session_state[f"{key_prefix}_shuffle_order"] = None
        st.session_state[f"{key_prefix}_wrong_indices"] = set()  # untuk menyimpan indeks soal yang salah

    # Sinkronkan panjang
    if len(st.session_state[f"{key_prefix}_answers"]) != len(data):
        st.session_state[f"{key_prefix}_answers"] = [None] * len(data)
        st.session_state[f"{key_prefix}_submitted"] = False
        st.session_state[f"{key_prefix}_shuffle_order"] = None
        st.session_state[f"{key_prefix}_wrong_indices"] = set()

    # Acak urutan jawaban
    if st.session_state[f"{key_prefix}_shuffle_order"] is None:
        jawaban_list = data["jawaban"].tolist()
        random.shuffle(jawaban_list)
        st.session_state[f"{key_prefix}_shuffle_order"] = jawaban_list

    shuffled_jawaban = st.session_state[f"{key_prefix}_shuffle_order"]

    # Tampilkan soal
    for idx in range(len(data)):
        row = data.iloc[idx]
        soal = row["soal"]
        pinyin_soal = row.get("pinyin1", "")
        arti_soal = row.get("arti1", "")
        
        # Tentukan apakah expander ini salah (setelah cek jawaban)
        is_wrong = (st.session_state[f"{key_prefix}_submitted"] and 
                    st.session_state[f"{key_prefix}_answers"][idx] != row["jawaban"])
        # Tambahkan class CSS untuk border merah jika salah
        expander_label = f"Soal {idx+1}: {soal}"
        if is_wrong:
            expander_label = f"❌ {expander_label}"
        
        with st.expander(expander_label):
            # Tombol pinyin
            pinyin_key = f"show_pinyin_{selected_kode}_{idx}"
            if st.button(f"🔊 Tampilkan Pinyin {idx+1}", key=f"pinyin_btn_{selected_kode}_{idx}"):
                st.session_state[pinyin_key] = not st.session_state.get(pinyin_key, False)
            if st.session_state.get(pinyin_key, False):
                st.caption(f"📖 Pinyin: {pinyin_soal}")

            # Jika sudah dijawab dan salah, tampilkan arti soal di dalam expander
            if is_wrong:
                st.warning(f"💡 Arti soal: {arti_soal}")

        # Dropdown untuk memilih jawaban
        current_ans = st.session_state[f"{key_prefix}_answers"][idx]
        default_idx = None
        if current_ans in shuffled_jawaban:
            default_idx = shuffled_jawaban.index(current_ans)
        st.session_state[f"{key_prefix}_answers"][idx] = st.selectbox(
            f"Pilih jawaban untuk soal {idx+1}",
            options=shuffled_jawaban,
            index=default_idx,
            key=f"match_{selected_kode}_{idx}",
            label_visibility="collapsed"
        )

    # Tombol cek jawaban
    if st.button("✅ Cek Jawaban", key=f"check_{selected_kode}", use_container_width=True):
        st.session_state[f"{key_prefix}_submitted"] = True
        all_correct = True
        wrong_indices = set()
        wrong_pairs = []
        for idx in range(len(data)):
            row = data.iloc[idx]
            user_ans = st.session_state[f"{key_prefix}_answers"][idx]
            correct_ans = row["jawaban"]
            if user_ans != correct_ans:
                all_correct = False
                wrong_indices.add(idx)
                wrong_pairs.append((idx+1, row["soal"], correct_ans, row.get("arti2", "")))
        st.session_state[f"{key_prefix}_wrong_indices"] = wrong_indices
        if all_correct:
            st.success("🎉 Semua jawaban tepat! Selamat.")
        else:
            st.error("❌ Masih ada jawaban yang salah. Perbaiki yang ditandai.")
            for nomor, soal, jawaban, arti in wrong_pairs:
                st.markdown(f"- **Soal {nomor}:** {soal} → jawaban benar: **{jawaban}** ({arti})")
        st.rerun()

    # Tombol reset
    if st.button("🔄 Reset jawaban", key=f"reset_{selected_kode}", use_container_width=True):
        for key in list(st.session_state.keys()):
            if key.startswith(f"match_{selected_kode}_") or key.startswith(f"show_pinyin_{selected_kode}_"):
                st.session_state.pop(key, None)
        st.session_state[f"{key_prefix}_answers"] = [None] * len(data)
        st.session_state[f"{key_prefix}_submitted"] = False
        st.session_state[f"{key_prefix}_shuffle_order"] = None
        st.session_state[f"{key_prefix}_wrong_indices"] = set()
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
elif st.session_state.menu == "Susun Jawaban":
    matching_view()
else:
    scramble_view()

save_progress()
