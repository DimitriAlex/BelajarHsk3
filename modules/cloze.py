import streamlit as st
import random
from modules.utils import render_speaker_button, rerun_app, render_top_dashboard


def cloze_view(cloze_df):
    """Tampilan isi kalimat kosong"""
    st.markdown("<div class='glass-card'><h2>✏️ Isi Kalimat Kosong</h2><p>Isi titik-titik dengan pilihan yang tepat.</p></div>", unsafe_allow_html=True)

    total_vocab = len(cloze_df) if cloze_df is not None else 0
    mastered_vocab = st.session_state.get("mastered_vocab", set())

    def total_score():
        return st.session_state.get("score_quiz", 0) + st.session_state.get("score_cloze", 0) + st.session_state.get("score_scramble", 0)

    def accuracy_percent():
        total_attempts = st.session_state.get("quiz_attempts", 0) + st.session_state.get("cloze_attempts", 0) + st.session_state.get("scramble_attempts", 0)
        total_correct = st.session_state.get("quiz_correct_attempts", 0) + st.session_state.get("cloze_correct_attempts", 0) + st.session_state.get("scramble_correct_attempts", 0)
        if total_attempts == 0:
            return 0
        return round((total_correct / total_attempts) * 100)

    render_top_dashboard(cloze_df if cloze_df is not None else None, mastered_vocab, total_score, accuracy_percent, st.session_state.get("current_streak", 0), total_vocab)

    if cloze_df is None or len(cloze_df) == 0:
        st.warning("Belum ada soal.")
        return

    total = len(cloze_df)
    pool = list(range(total))
    if st.session_state.get("rep_mode") == "Soal Salah Saja":
        wrong_set = st.session_state.get("wrong_cloze", set())
        if wrong_set:
            pool = list(wrong_set)
        else:
            st.info("Semua soal di mode ini sudah beres. Kembali ke mode Normal.")
            st.session_state.rep_mode = "Normal"
            rerun_app()
            return

    if not pool:
        return

    idx = st.session_state.get("clz_idx", 0) % len(pool)
    question_idx = pool[idx]
    soal = cloze_df.iloc[question_idx]

    if not st.session_state.get("clz_options"):
        pilihan = [soal["pilihan1"], soal["pilihan2"], soal["pilihan3"], soal["pilihan4"]]
        pilihan = [opt for opt in pilihan if opt]
        random.shuffle(pilihan)
        st.session_state.clz_options = pilihan
        st.session_state.clz_answered = False
        st.session_state.clz_feedback = None
        st.session_state.current_kalimat = soal["kalimat"]
        st.session_state.current_benar_cloze = soal["jawaban_benar"]
        st.session_state.pinyin_kal = soal.get("pinyin", "")
        st.session_state.current_alasan = soal.get("alasan", "")

    st.progress((idx + 1) / len(pool))
    st.caption(f"Soal {idx+1} dari {len(pool)}")

    col_kal, col_spk = st.columns([4, 1])
    with col_kal:
        st.markdown(f"<div class='glass-card'>{st.session_state.current_kalimat}</div>", unsafe_allow_html=True)
    with col_spk:
        render_speaker_button(st.session_state.current_kalimat, f"cloze_soal_{question_idx}")

    if st.button("🔊 Tampilkan Pinyin Kalimat", key="clz_pin"):
        st.session_state.clz_show_pinyin = not st.session_state.get("clz_show_pinyin", False)
        rerun_app()

    if st.session_state.get("clz_show_pinyin", False) and st.session_state.pinyin_kal:
        st.caption(f"Pinyin: {st.session_state.pinyin_kal}")

    if not st.session_state.get("clz_answered", False):
        cols = st.columns(2)
        for i, opt in enumerate(st.session_state.clz_options):
            with cols[i % 2]:
                col_btn, col_opt_spk = st.columns([4, 1])
                with col_btn:
                    if st.button(opt, key=f"clz_{question_idx}_{i}", use_container_width=True):
                        st.session_state.clz_answered = True
                        st.session_state.cloze_attempts = st.session_state.get("cloze_attempts", 0) + 1
                        is_correct = opt == st.session_state.current_benar_cloze
                        st.session_state.user_answer = opt
                        if is_correct:
                            st.session_state.cloze_correct_attempts = st.session_state.get("cloze_correct_attempts", 0) + 1
                            if question_idx not in st.session_state.get("cloze_answered_set", set()):
                                st.session_state.score_cloze = st.session_state.get("score_cloze", 0) + 10
                                st.session_state.cloze_answered_set.add(question_idx)
                            st.session_state.wrong_cloze.discard(question_idx)
                            st.session_state.clz_feedback = "correct"
                        else:
                            st.session_state.wrong_cloze.add(question_idx)
                            st.session_state.clz_feedback = "wrong"
                        # update streak
                        if is_correct:
                            st.session_state.current_streak = st.session_state.get("current_streak", 0) + 1
                            st.session_state.best_streak = max(st.session_state.get("best_streak", 0), st.session_state.current_streak)
                        else:
                            st.session_state.current_streak = 0
                        rerun_app()
                with col_opt_spk:
                    render_speaker_button(opt, f"cloze_opt_{question_idx}_{i}")
    else:
        st.markdown("### 📋 Hasil Jawaban")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**📝 Kalimat soal**")
            st.info(st.session_state.current_kalimat)
            st.markdown("**❌ Jawaban Anda**")
            user_ans = st.session_state.user_answer if hasattr(st.session_state, 'user_answer') else "-"
            color = "green" if st.session_state.clz_feedback == "correct" else "red"
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
            st.session_state.clz_idx = (idx + 1) % len(pool)
            st.session_state.clz_options = []
            st.session_state.clz_answered = False
            st.session_state.clz_feedback = None
            if 'user_answer' in st.session_state:
                del st.session_state.user_answer
            rerun_app()

    st.metric("Skor Isi Kalimat", st.session_state.get("score_cloze", 0))