import streamlit as st
import random
from copy import deepcopy
import jieba
from modules.utils import render_speaker_button, rerun_app, render_top_dashboard


def scramble_view(scramble_df):
    """Tampilan susun kalimat acak"""
    st.markdown("<div class='glass-card'><h2>🔄 Susun Kalimat Acak</h2><p>Susun kata-kata menjadi kalimat yang benar.</p></div>", unsafe_allow_html=True)

    total_vocab = 0
    mastered_vocab = st.session_state.get("mastered_vocab", set())

    def total_score():
        return st.session_state.get("score_quiz", 0) + st.session_state.get("score_cloze", 0) + st.session_state.get("score_scramble", 0)

    def accuracy_percent():
        total_attempts = st.session_state.get("quiz_attempts", 0) + st.session_state.get("cloze_attempts", 0) + st.session_state.get("scramble_attempts", 0)
        total_correct = st.session_state.get("quiz_correct_attempts", 0) + st.session_state.get("cloze_correct_attempts", 0) + st.session_state.get("scramble_correct_attempts", 0)
        if total_attempts == 0:
            return 0
        return round((total_correct / total_attempts) * 100)

    render_top_dashboard(None, mastered_vocab, total_score, accuracy_percent, st.session_state.get("current_streak", 0), total_vocab)

    if scramble_df is None or len(scramble_df) == 0:
        st.warning("Belum ada soal.")
        return

    total = len(scramble_df)
    pool = list(range(total))
    if st.session_state.get("rep_mode") == "Soal Salah Saja":
        wrong_set = st.session_state.get("wrong_scramble", set())
        if wrong_set:
            pool = list(wrong_set)
        else:
            st.info("Semua soal di mode ini sudah beres. Kembali ke mode Normal.")
            st.session_state.rep_mode = "Normal"
            rerun_app()
            return

    if not pool:
        return

    idx = st.session_state.get("sc_idx", 0) % len(pool)
    question_idx = pool[idx]
    original_text = str(scramble_df.iloc[question_idx].get("kalimat_asli", ""))

    if st.session_state.get("sc_idx") != idx or not st.session_state.get("sc_original"):
        tokens = [t for t in jieba.cut(original_text) if t.strip()]
        st.session_state.sc_original = tokens
        st.session_state.sc_tokens = deepcopy(tokens)
        random.shuffle(st.session_state.sc_tokens)
        st.session_state.sc_order = []
        st.session_state.sc_answered = False
        st.session_state.sc_feedback = None
        st.session_state.current_pola = scramble_df.iloc[question_idx].get("pola", "")

    st.progress((idx + 1) / len(pool))
    st.caption(f"Soal {idx+1} dari {len(pool)}")

    col_info, col_spk = st.columns([4, 1])
    with col_info:
        st.markdown("**🔀 Susun kata-kata menjadi kalimat yang benar:**")
    with col_spk:
        render_speaker_button(original_text, f"scramble_soal_{question_idx}")

    if not st.session_state.get("sc_answered", False):
        if st.session_state.sc_tokens:
            cols = st.columns(min(4, len(st.session_state.sc_tokens)))
            for i, tok in enumerate(st.session_state.sc_tokens):
                with cols[i % len(cols)]:
                    col_tok, col_tok_spk = st.columns([4, 1])
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
                st.session_state.scramble_attempts = st.session_state.get("scramble_attempts", 0) + 1
                joined_answer = "".join(st.session_state.sc_order).replace(" ", "")
                joined_original = "".join(st.session_state.sc_original).replace(" ", "")
                is_correct = joined_answer == joined_original
                st.session_state.user_answer = " ".join(st.session_state.sc_order) if st.session_state.sc_order else "(kosong)"

                if is_correct:
                    st.session_state.scramble_correct_attempts = st.session_state.get("scramble_correct_attempts", 0) + 1
                    st.session_state.sc_feedback = "correct"
                    if question_idx not in st.session_state.get("scramble_scored_set", set()):
                        st.session_state.score_scramble = st.session_state.get("score_scramble", 0) + 10
                        st.session_state.scramble_scored_set.add(question_idx)
                    st.session_state.wrong_scramble.discard(question_idx)
                else:
                    st.session_state.sc_feedback = "wrong"
                    st.session_state.wrong_scramble.add(question_idx)

                # update streak
                if is_correct:
                    st.session_state.current_streak = st.session_state.get("current_streak", 0) + 1
                    st.session_state.best_streak = max(st.session_state.get("best_streak", 0), st.session_state.current_streak)
                else:
                    st.session_state.current_streak = 0

                rerun_app()
    else:
        st.markdown("### 📋 Hasil Jawaban")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**📝 Kalimat asli (soal)**")
            st.info(' '.join(st.session_state.sc_original))
            st.markdown("**❌ Urutan Anda**")
            user_ans = st.session_state.user_answer if hasattr(st.session_state, 'user_answer') else "-"
            color = "green" if st.session_state.sc_feedback == "correct" else "red"
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
                st.session_state.sc_idx = (idx + 1) % len(pool)
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

    st.metric("Skor Susun Kalimat", st.session_state.get("score_scramble", 0))