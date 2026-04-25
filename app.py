import streamlit as st
import pandas as pd
import random
import jieba
from copy import deepcopy
import os

st.set_page_config(
    page_title="HSK 3 Master | Modern Learning",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ------------------------ CSS ULTRA MODERN (2026) ------------------------
st.markdown("""
<style>
    /* (CSS tetap seperti sebelumnya, tidak perlu diubah) */
    @import url('https://fonts.googleapis.com/css2?family=Inter:opsz,wght@14..32,300;14..32,500;14..32,700;14..32,800&display=swap');
    * { font-family: 'Inter', sans-serif; }
    .stApp { background: radial-gradient(circle at 10% 30%, #f9faff, #eef2ff); backdrop-filter: blur(2px); }
    [data-testid="stSidebar"] { background: rgba(255, 255, 255, 0.6); backdrop-filter: blur(20px); border-right: 1px solid rgba(255,255,255,0.5); box-shadow: 4px 0 20px rgba(0,0,0,0.02); }
    .glass-card { background: rgba(255, 255, 255, 0.75); backdrop-filter: blur(16px); border-radius: 38px; padding: 28px 24px; border: 1px solid rgba(255,255,255,0.6); box-shadow: 0 20px 35px -12px rgba(0,0,0,0.05); transition: all 0.2s ease; }
    .hanzi-giant { font-size: clamp(3.5rem, 12vw, 7rem); font-weight: 800; letter-spacing: 2px; background: linear-gradient(135deg, #1e2b6e, #2b3f8e); -webkit-background-clip: text; background-clip: text; color: transparent; text-align: center; line-height: 1.2; margin: 0.5rem 0; }
    .pinyin-chip { background: rgba(59,130,246,0.15); border-radius: 60px; padding: 6px 18px; font-weight: 500; font-size: 0.9rem; color: #1e40af; display: inline-block; backdrop-filter: blur(4px); }
    div.stButton > button { background: white; border: none; border-radius: 48px; padding: 12px 16px; font-weight: 600; font-size: 0.9rem; transition: all 0.25s ease; box-shadow: 0 1px 2px rgba(0,0,0,0.02); border: 1px solid rgba(0,0,0,0.04); width: 100%; }
    div.stButton > button:hover { transform: translateY(-3px); box-shadow: 0 12px 22px -12px rgba(59,130,246,0.3); border-color: #3b82f6; background: #fafcff; }
    .grid-floating { display: flex; flex-wrap: wrap; gap: 14px; justify-content: center; margin: 20px 0; }
    .grid-floating button { flex: 1 1 100px; max-width: 130px; font-size: 1.1rem; padding: 12px 6px; border-radius: 28px; background: rgba(255,255,240,0.7); backdrop-filter: blur(8px); border: 1px solid rgba(255,255,255,0.8); }
    @media (max-width: 640px) { .grid-floating button { flex: 1 1 75px; font-size: 0.9rem; } }
    .sidebar-title { font-weight: 700; letter-spacing: -0.3px; margin-bottom: 1rem; font-size: 1.2rem; }
    .score-modern { background: linear-gradient(105deg, #3b82f6, #2563eb); border-radius: 32px; padding: 16px; text-align: center; color: white; margin-bottom: 24px; box-shadow: 0 8px 18px -6px #3b82f670; }
</style>
""", unsafe_allow_html=True)

# ------------------------ LOAD DATA ------------------------
@st.cache_data
def load_data():
    if not os.path.exists("hsk3.xlsx"):
        return None, None, None
    vocab = pd.read_excel("hsk3.xlsx", sheet_name="Kosa_kata")
    cloze = pd.read_excel("hsk3.xlsx", sheet_name="Kalimat_kosong")
    scramble = pd.read_excel("hsk3.xlsx", sheet_name="Acak")
    return vocab, cloze, scramble

vocab, cloze, scramble = load_data()
if vocab is None:
    st.error("❌ File hsk3.xlsx tidak ditemukan.")
    st.stop()

total_vocab = len(vocab)

# ------------------------ SESSION STATE INIT ------------------------
if 'menu' not in st.session_state:
    st.session_state.menu = "📇 Flashcard"
if 'fc_page' not in st.session_state:
    st.session_state.fc_page = 0
if 'selected_hanzi' not in st.session_state:
    st.session_state.selected_hanzi = None
if 'score_quiz' not in st.session_state:
    st.session_state.score_quiz = 0
if 'score_cloze' not in st.session_state:
    st.session_state.score_cloze = 0
if 'score_scramble' not in st.session_state:
    st.session_state.score_scramble = 0
if 'quiz_answered_set' not in st.session_state:
    st.session_state.quiz_answered_set = set()
if 'cloze_answered_set' not in st.session_state:
    st.session_state.cloze_answered_set = set()
if 'scramble_scored_set' not in st.session_state:
    st.session_state.scramble_scored_set = set()
    # Di bagian inisialisasi session state
if 'wrong_quiz' not in st.session_state:
    st.session_state.wrong_quiz = set()   # indeks soal kuis yang pernah salah
if 'wrong_cloze' not in st.session_state:
    st.session_state.wrong_cloze = set()  # indeks soal cloze yang pernah salah
if 'rep_mode' not in st.session_state:
    st.session_state.rep_mode = "Normal"  # "Normal" atau "Salah Saja"

# Quiz internal
if 'quiz_idx' not in st.session_state:
    st.session_state.quiz_idx = 0
    st.session_state.quiz_options = []
    st.session_state.quiz_answered = False
    st.session_state.quiz_show_pinyin = False
    st.session_state.quiz_mode = "Hanzi → Arti"
    st.session_state.quiz_feedback = None

# Cloze internal
if 'clz_idx' not in st.session_state:
    st.session_state.clz_idx = 0
    st.session_state.clz_options = []
    st.session_state.clz_answered = False
    st.session_state.clz_show_pinyin = False
    st.session_state.clz_feedback = None

# Scramble internal — PERBAIKAN: tambahkan sc_answered dan sc_feedback
if 'sc_idx' not in st.session_state:
    st.session_state.sc_idx = 0
    st.session_state.sc_tokens = []
    st.session_state.sc_order = []
    st.session_state.sc_original = []
    st.session_state.sc_answered = False    # <--- kunci perbaikan
    st.session_state.sc_feedback = None     # <--- kunci perbaikan

# ------------------------ SIDEBAR ------------------------
with st.sidebar:
    st.markdown(f"""
    <div class="score-modern">
        <span style="font-size:0.8rem; opacity:0.8;">TOTAL SCORE</span><br>
        <span style="font-size:2.2rem; font-weight:800;">{st.session_state.score_quiz + st.session_state.score_cloze + st.session_state.score_scramble}</span>
    </div>
    
    
    """, unsafe_allow_html=True)
    st.markdown("<div class='sidebar-title'>📌 Menu</div>", unsafe_allow_html=True)
    for lbl in ["📇 Flashcard", "📝 Kuis Kosakata", "✏️ Isi Kalimat", "🔄 Susun Kalimat"]:
        if st.button(lbl, key=f"menu_{lbl}", use_container_width=True):
            st.session_state.menu = lbl
            st.session_state.selected_hanzi = None
            if lbl != "📝 Kuis Kosakata":
                st.session_state.quiz_answered = False
                st.session_state.quiz_options = []
            st.rerun()
    st.divider()
    if st.button("🗑️ Reset seluruh skor", use_container_width=True):
        st.session_state.score_quiz = 0
        st.session_state.score_cloze = 0
        st.session_state.score_scramble = 0
        st.session_state.quiz_answered_set.clear()
        st.session_state.cloze_answered_set.clear()
        st.session_state.scramble_scored_set.clear()
        st.rerun()
    st.markdown("---")
    st.caption(f"✨ Kuis : {st.session_state.score_quiz}")
    st.caption(f"📝 Isi Kalimat : {st.session_state.score_cloze}")
    st.caption(f"🔄 Susun : {st.session_state.score_scramble}")

# ==================== FLASHCARD ====================
def flashcard_view():
    st.markdown("<div class='glass-card'><h2 style='margin:0'>📇 Flashcard</h2><p style='margin-bottom:0'>Klik kosakata, lihat arti & contoh</p></div>", unsafe_allow_html=True)
    per_page = 24
    total_pages = (total_vocab - 1)//per_page + 1
    start = st.session_state.fc_page * per_page
    end = min(start+per_page, total_vocab)

    col1, col2, col3 = st.columns([1,2,1])
    with col1:
        if st.button("◀", disabled=st.session_state.fc_page==0):
            st.session_state.fc_page -= 1
            st.rerun()
    with col2:
        st.markdown(f"<div style='text-align:center'>Halaman {st.session_state.fc_page+1} / {total_pages}</div>", unsafe_allow_html=True)
    with col3:
        if st.button("▶", disabled=st.session_state.fc_page>=total_pages-1):
            st.session_state.fc_page += 1
            st.rerun()

    if st.session_state.selected_hanzi is None:
        st.markdown('<div class="grid-floating">', unsafe_allow_html=True)
        for i in range(start, end):
            han = vocab.iloc[i]['Kosakata']
            if st.button(han, key=f"fc_{i}", use_container_width=True):
                st.session_state.selected_hanzi = i
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        item = vocab.iloc[st.session_state.selected_hanzi]
        st.markdown(f"""
        <div class="glass-card" style="text-align:center">
            <div class="hanzi-giant">{item['Kosakata']}</div>
            <div><span class="pinyin-chip">{item['Pinyin']}</span></div>
            <hr>
            <p style="font-weight:700; margin:0">Arti</p>
            <p style="font-size:1.2rem">{item['Arti Indonesia']}</p>
            <p style="font-weight:500">📖 Contoh</p>
            <p>{item['Contoh'] if pd.notna(item['Contoh']) else '—'}</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("⬅ Kembali ke daftar", use_container_width=True):
            st.session_state.selected_hanzi = None
            st.rerun()

# ==================== KUIS KOSAKATA ====================
def kuis_view():
    st.markdown("<div class='glass-card'><h2 style='margin:0'>📝 Kuis Kosakata</h2></div>", unsafe_allow_html=True)
    mode = st.radio("Pilih mode", ["Hanzi → Arti", "Arti → Hanzi"], horizontal=True)
    if mode != st.session_state.quiz_mode:
        st.session_state.quiz_mode = mode
        st.session_state.quiz_options = []
        st.session_state.quiz_answered = False
        st.session_state.quiz_feedback = None
        st.rerun()

    total = total_vocab
    if total == 0:
        st.warning("Tidak ada data kosakata.")
        return

    idx = st.session_state.quiz_idx % total

    if not st.session_state.quiz_options:
        item = vocab.iloc[idx]
        if st.session_state.quiz_mode == "Hanzi → Arti":
            soal = item['Kosakata']
            benar = item['Arti Indonesia']
            other_indices = [i for i in range(total) if i != idx]
            random.shuffle(other_indices)
            others = []
            for i in other_indices:
                art = vocab.iloc[i]['Arti Indonesia']
                if art != benar and art not in others:
                    others.append(art)
                if len(others) == 3:
                    break
            while len(others) < 3:
                others.append("???")
            pilihan = [benar] + others
            random.shuffle(pilihan)
        else:
            soal = item['Arti Indonesia']
            benar = item['Kosakata']
            other_indices = [i for i in range(total) if i != idx]
            random.shuffle(other_indices)
            others = []
            for i in other_indices:
                han = vocab.iloc[i]['Kosakata']
                if han != benar and han not in others:
                    others.append(han)
                if len(others) == 3:
                    break
            while len(others) < 3:
                others.append("???")
            pilihan = [benar] + others
            random.shuffle(pilihan)

        st.session_state.quiz_options = pilihan
        st.session_state.quiz_answered = False
        st.session_state.quiz_feedback = None
        st.session_state.current_soal = soal
        st.session_state.current_benar = benar
        st.session_state.current_pinyin = vocab.iloc[idx]['Pinyin']

    st.markdown(f"<div class='hanzi-giant'>{st.session_state.current_soal}</div>", unsafe_allow_html=True)

    if st.button("🔊 Tampilkan Pinyin", key="quiz_pin"):
        st.session_state.quiz_show_pinyin = not st.session_state.quiz_show_pinyin
        st.rerun()
    if st.session_state.quiz_show_pinyin:
        st.markdown(f"<div style='text-align:center'><span class='pinyin-chip'>{st.session_state.current_pinyin}</span></div>", unsafe_allow_html=True)

    if not st.session_state.quiz_answered:
        cols = st.columns(2)
        for i, opt in enumerate(st.session_state.quiz_options):
            with cols[i % 2]:
                if st.button(opt, key=f"quiz_{idx}_{i}", use_container_width=True):
                    st.session_state.quiz_answered = True
                    if opt == st.session_state.current_benar:
                        if idx not in st.session_state.quiz_answered_set:
                            st.session_state.score_quiz += 10
                            st.session_state.quiz_answered_set.add(idx)
                        st.session_state.quiz_feedback = "correct"
                    else:
                        st.session_state.quiz_feedback = "wrong"
                    st.rerun()
    else:
        if st.session_state.quiz_feedback == "correct":
            st.success("✅ Benar!")
        else:
            st.error(f"❌ Salah. Jawaban benar: {st.session_state.current_benar}")
        if st.button("➡️ Soal berikutnya", type="primary", use_container_width=True):
            st.session_state.quiz_idx = (idx + 1) % total
            st.session_state.quiz_options = []
            st.session_state.quiz_answered = False
            st.session_state.quiz_feedback = None
            st.rerun()
    st.metric("Skor Kuis", st.session_state.score_quiz)

# ==================== ISI KALIMAT KOSONG ====================
# ==================== ISI KALIMAT KOSONG (dengan alasan) ====================
def cloze_view():
    st.markdown("<div class='glass-card'><h2 style='margin:0'>✏️ Isi Kalimat Kosong</h2></div>", unsafe_allow_html=True)
    if cloze is None or len(cloze) == 0:
        st.warning("Belum ada soal di sheet 'Kalimat_kosong'.")
        return
    total = len(cloze)
    idx = st.session_state.clz_idx % total
    soal = cloze.iloc[idx]

    if not st.session_state.clz_options:
        kalimat = soal['kalimat']
        benar = soal['jawaban_benar']
        pilihan = [soal['pilihan1'], soal['pilihan2'], soal['pilihan3'], soal['pilihan4']]
        random.shuffle(pilihan)
        st.session_state.clz_options = pilihan
        st.session_state.clz_answered = False
        st.session_state.clz_feedback = None
        st.session_state.current_kalimat = kalimat
        st.session_state.current_benar_cloze = benar
        st.session_state.pinyin_kal = soal['pinyin'] if 'pinyin' in cloze.columns else ""
        # Ambil alasan jika ada
        st.session_state.current_alasan = soal['alasan'] if 'alasan' in cloze.columns else ""

    st.markdown(f"<div class='glass-card'>{st.session_state.current_kalimat}</div>", unsafe_allow_html=True)

    if st.button("🔊 Tampilkan Pinyin Kalimat", key="clz_pin"):
        st.session_state.clz_show_pinyin = not st.session_state.clz_show_pinyin
        st.rerun()
    if st.session_state.clz_show_pinyin and st.session_state.pinyin_kal:
        st.caption(f"Pinyin: {st.session_state.pinyin_kal}")

    if not st.session_state.clz_answered:
        cols = st.columns(2)
        for i, opt in enumerate(st.session_state.clz_options):
            with cols[i % 2]:
                if st.button(opt, key=f"clz_{idx}_{i}", use_container_width=True):
                    st.session_state.clz_answered = True
                    if opt == st.session_state.current_benar_cloze:
                        if idx not in st.session_state.cloze_answered_set:
                            st.session_state.score_cloze += 10
                            st.session_state.cloze_answered_set.add(idx)
                        st.session_state.clz_feedback = "correct"
                    else:
                        st.session_state.clz_feedback = "wrong"
                        # Catat sebagai soal salah untuk repitisi
                        st.session_state.wrong_cloze.add(idx)
                    st.rerun()
    else:
        if st.session_state.clz_feedback == "correct":
            st.success("✅ Tepat!")
        else:
            st.error(f"❌ Jawaban benar: {st.session_state.current_benar_cloze}")
            # Tampilkan alasan penjelasan jika ada
            if st.session_state.current_alasan:
                st.info(f"📖 Penjelasan: {st.session_state.current_alasan}")
        if st.button("📌 Soal berikutnya", use_container_width=True):
            st.session_state.clz_idx = (idx + 1) % total
            st.session_state.clz_options = []
            st.session_state.clz_answered = False
            st.session_state.clz_feedback = None
            st.rerun()
    st.metric("Skor Isi Kalimat", st.session_state.score_cloze)

# ==================== SUSUN KALIMAT (dengan perbaikan) ====================
# ==================== SUSUN KALIMAT (dengan pola grammar) ====================
def scramble_view():
    st.markdown("<div class='glass-card'><h2 style='margin:0'>🔄 Susun Kalimat Acak</h2></div>", unsafe_allow_html=True)
    if scramble is None or len(scramble) == 0:
        st.warning("Belum ada soal di sheet 'Acak'.")
        return
    total = len(scramble)
    idx = st.session_state.sc_idx % total
    original_text = scramble.iloc[idx]['kalimat_asli']

    if st.session_state.sc_idx != idx or not st.session_state.sc_original:
        tokens = [t for t in jieba.cut(original_text) if t.strip()]
        st.session_state.sc_original = tokens
        st.session_state.sc_tokens = deepcopy(tokens)
        random.shuffle(st.session_state.sc_tokens)
        st.session_state.sc_order = []
        st.session_state.sc_answered = False
        st.session_state.sc_feedback = None
        # Ambil pola grammar jika ada
        st.session_state.current_pola = scramble.iloc[idx]['pola'] if 'pola' in scramble.columns else ""

    st.markdown("**📌 Susun kata-kata di bawah menjadi kalimat yang benar**")

    if not st.session_state.sc_answered:
        if st.session_state.sc_tokens:
            cols = st.columns(min(4, len(st.session_state.sc_tokens)))
            for i, tok in enumerate(st.session_state.sc_tokens):
                with cols[i % len(cols)]:
                    if st.button(tok, key=f"sc_{idx}_{i}_{tok}", use_container_width=True):
                        st.session_state.sc_order.append(tok)
                        st.session_state.sc_tokens.pop(i)
                        st.rerun()
        else:
            st.info("✅ Semua kata sudah disusun. Klik 'Cek Jawaban'.")

        if st.session_state.sc_order:
            st.markdown("**Urutan Anda:** " + " ".join(st.session_state.sc_order))

        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("🔄 Reset", use_container_width=True):
                st.session_state.sc_tokens = deepcopy(st.session_state.sc_original)
                random.shuffle(st.session_state.sc_tokens)
                st.session_state.sc_order = []
                st.rerun()
        with col_b:
            if st.button("✅ Cek Jawaban", use_container_width=True):
                st.session_state.sc_answered = True
                if st.session_state.sc_order == st.session_state.sc_original:
                    st.session_state.sc_feedback = "correct"
                    if idx not in st.session_state.scramble_scored_set:
                        st.session_state.score_scramble += 10
                        st.session_state.scramble_scored_set.add(idx)
                else:
                    st.session_state.sc_feedback = "wrong"
                st.rerun()
    else:
        if st.session_state.sc_feedback == "correct":
            st.success("✅ Kalimat benar!")
        else:
            st.error(f"❌ Urutan yang benar: {' '.join(st.session_state.sc_original)}")
            # Tampilkan pola grammar jika ada
            if st.session_state.current_pola:
                st.info(f"📖 Pola grammar: {st.session_state.current_pola}")

        col_next, col_tryagain = st.columns(2)
        with col_next:
            if st.button("➡️ Soal berikutnya", type="primary", use_container_width=True):
                st.session_state.sc_idx = (idx + 1) % total
                st.session_state.sc_tokens = []
                st.session_state.sc_original = []
                st.session_state.sc_order = []
                st.session_state.sc_answered = False
                st.session_state.sc_feedback = None
                st.rerun()
        with col_tryagain:
            if st.button("🔄 Coba lagi soal ini", use_container_width=True):
                st.session_state.sc_tokens = deepcopy(st.session_state.sc_original)
                random.shuffle(st.session_state.sc_tokens)
                st.session_state.sc_order = []
                st.session_state.sc_answered = False
                st.session_state.sc_feedback = None
                st.rerun()

    col_prev, col_next_soal = st.columns(2)
    with col_prev:
        if st.button("◀ Sebelum", use_container_width=True):
            st.session_state.sc_idx = (idx - 1) % total
            st.session_state.sc_tokens = []
            st.session_state.sc_original = []
            st.session_state.sc_order = []
            st.session_state.sc_answered = False
            st.session_state.sc_feedback = None
            st.rerun()
    with col_next_soal:
        if st.button("Berikutnya ▶", use_container_width=True):
            st.session_state.sc_idx = (idx + 1) % total
            st.session_state.sc_tokens = []
            st.session_state.sc_original = []
            st.session_state.sc_order = []
            st.session_state.sc_answered = False
            st.session_state.sc_feedback = None
            st.rerun()

    st.metric("Skor Susun Kalimat", st.session_state.score_scramble)
# ==================== ROUTER ====================
if st.session_state.menu == "📇 Flashcard":
    flashcard_view()
elif st.session_state.menu == "📝 Kuis Kosakata":
    kuis_view()
elif st.session_state.menu == "✏️ Isi Kalimat":
    cloze_view()
else:
    scramble_view()