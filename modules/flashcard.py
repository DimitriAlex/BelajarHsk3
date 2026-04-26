import streamlit as st
from modules.utils import render_speaker_button, rerun_app, render_top_dashboard


def build_flashcard_indices(vocab_df, search_text, hide_mastered, mastered_vocab):
    """Membangun indeks flashcard berdasarkan pencarian dan filter"""
    search_text = search_text.strip().lower()
    result = []
    for idx, row in vocab_df.iterrows():
        haystack = " ".join([
            str(row.get("Kosakata", "")),
            str(row.get("Pinyin", "")),
            str(row.get("Arti Indonesia", "")),
            str(row.get("Contoh", ""))
        ]).lower()
        if search_text and search_text not in haystack:
            continue
        if hide_mastered and idx in mastered_vocab:
            continue
        result.append(idx)
    return result


def flashcard_view(vocab_df):
    """Tampilan flashcard"""
    st.markdown("<div class='glass-card'><h2>📇 Flashcard</h2><p>Cari kosakata, tandai favorit, lalu simpan yang sudah dikuasai.</p></div>", unsafe_allow_html=True)

    total_vocab = len(vocab_df)
    mastered_vocab = st.session_state.get("mastered_vocab", set())
    favorites = st.session_state.get("favorites", set())

    def total_score():
        return st.session_state.get("score_quiz", 0) + st.session_state.get("score_cloze", 0) + st.session_state.get("score_scramble", 0)

    def accuracy_percent():
        total_attempts = st.session_state.get("quiz_attempts", 0) + st.session_state.get("cloze_attempts", 0) + st.session_state.get("scramble_attempts", 0)
        total_correct = st.session_state.get("quiz_correct_attempts", 0) + st.session_state.get("cloze_correct_attempts", 0) + st.session_state.get("scramble_correct_attempts", 0)
        if total_attempts == 0:
            return 0
        return round((total_correct / total_attempts) * 100)

    render_top_dashboard(vocab_df, mastered_vocab, total_score, accuracy_percent, st.session_state.get("current_streak", 0), total_vocab)

    search_col, info_col = st.columns([2, 1])
    with search_col:
        search_value = st.text_input("Cari Hanzi / Pinyin / Arti", value=st.session_state.get("flashcard_search", ""), placeholder="mis. 学校 / xuexiao / sekolah")
        if search_value != st.session_state.get("flashcard_search", ""):
            st.session_state.flashcard_search = search_value
            st.session_state.fc_page = 0
            rerun_app()
    with info_col:
        hide_mastered = st.toggle("Sembunyikan yang dikuasai", value=st.session_state.get("hide_mastered", True))
        if hide_mastered != st.session_state.get("hide_mastered", True):
            st.session_state.hide_mastered = hide_mastered
            st.session_state.fc_page = 0
            rerun_app()
        st.markdown(f"<div class='hint-box'>Favorit: {len(favorites)}<br>Dikuasai: {len(mastered_vocab)}</div>", unsafe_allow_html=True)

    visible_indices = build_flashcard_indices(vocab_df, st.session_state.get("flashcard_search", ""), st.session_state.get("hide_mastered", True), mastered_vocab)

    if not visible_indices:
        st.info("Tidak ada flashcard yang cocok.")
        if st.button("Reset pencarian"):
            st.session_state.flashcard_search = ""
            st.session_state.fc_page = 0
            rerun_app()
        if st.session_state.get("hide_mastered", True) and st.button("Tampilkan yang dikuasai"):
            st.session_state.hide_mastered = False
            st.session_state.fc_page = 0
            rerun_app()
        return

    per_page = 24
    total_pages = (len(visible_indices) - 1) // per_page + 1
    current_page = st.session_state.get("fc_page", 0)
    current_page = min(current_page, max(total_pages - 1, 0))
    start = current_page * per_page
    current_page_indices = visible_indices[start:start + per_page]

    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        if st.button("◀", disabled=current_page == 0):
            st.session_state.fc_page = current_page - 1
            rerun_app()
    with col2:
        st.markdown(f"<div style='text-align:center'>Halaman {current_page + 1} / {total_pages}</div>", unsafe_allow_html=True)
    with col3:
        if st.button("▶", disabled=current_page >= total_pages - 1):
            st.session_state.fc_page = current_page + 1
            rerun_app()

    if st.session_state.get("selected_hanzi") is None:
        st.markdown('<div class="grid-floating">', unsafe_allow_html=True)
        cols = st.columns(4)
        for pos, idx in enumerate(current_page_indices):
            row = vocab_df.iloc[idx]
            label = row["Kosakata"]
            if idx in favorites:
                label = f"⭐ {label}"
            with cols[pos % 4]:
                if st.button(label, key=f"fc_{idx}", use_container_width=True):
                    st.session_state.selected_hanzi = idx
                    rerun_app()
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        idx = st.session_state.selected_hanzi
        item = vocab_df.iloc[idx]
        example = item["Contoh"] if item["Contoh"] else "Belum ada contoh kalimat."
        st.markdown(f"""<div class="glass-card" style="text-align:center"><div class="hanzi-giant">{item['Kosakata']}</div><div><span class="pinyin-chip">{item['Pinyin']}</span></div><hr><p style="font-weight:700; margin:0">Arti</p><p>{item['Arti Indonesia']}</p><p style="font-weight:500">Contoh</p><p>{example}</p></div>""", unsafe_allow_html=True)

        col_spk1, col_spk2 = st.columns([1, 1])
        with col_spk1:
            render_speaker_button(item['Kosakata'], f"fc_hanzi_{idx}")
        with col_spk2:
            if example and example != "Belum ada contoh kalimat.":
                render_speaker_button(example, f"fc_contoh_{idx}")

        btn1, btn2, btn3 = st.columns(3)
        with btn1:
            if st.button("⭐ Simpan Favorit" if idx not in favorites else "✅ Favorit Tersimpan", use_container_width=True):
                st.session_state.favorites.add(idx)
                rerun_app()
        with btn2:
            if st.button("✔️ Tandai Dikuasai" if idx not in mastered_vocab else "✅ Sudah Dikuasai", use_container_width=True):
                st.session_state.mastered_vocab.add(idx)
                st.session_state.selected_hanzi = None
                rerun_app()
        with btn3:
            if st.button("⬅ Kembali ke daftar", use_container_width=True):
                st.session_state.selected_hanzi = None
                rerun_app()