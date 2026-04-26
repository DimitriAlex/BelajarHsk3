import streamlit as st
import random
from modules.utils import render_speaker_button, rerun_app, render_top_dashboard


def build_quiz_pool(total, wrong_set, rep_mode, rerun_app_func):
    """Membangun pool soal untuk kuis"""
    if rep_mode == "Soal Salah Saja":
        if wrong_set:
            return list(wrong_set)
        st.info("Semua soal di mode ini sudah beres. Kembali ke mode Normal.")
        st.session_state.rep_mode = "Normal"
        rerun_app_func()
    return list(range(total))


def kuis_view(vocab_df):
    """Tampilan kuis kosakata"""
    st.markdown("<div class='glass-card'><h2>📝 Kuis Kosakata</h2><p>Pilih arti yang tepat.</p></div>", unsafe_allow_html=True)

    total_vocab = len(vocab_df)
    mastered_vocab = st.session_state.get("mastered_vocab", set())

    def total_score():
        return st.session_state.get("score_quiz", 0) + st.session_state.get("score_cloze", 0) + st.session_state.get("score_scramble", 0)

    def accuracy_percent():
        total_attempts = st.session_state.get("quiz_attempts", 0) + st.session_state.get("cloze_attempts", 0) + st.session_state.get("scramble_attempts", 0)
        total_correct = st.session_state.get("quiz_correct_attempts", 0) + st.session_state.get("cloze_correct_attempts", 0) + st.session_state.get("scramble_correct_attempts", 0)
        if total_attempts == 0:
            return 0
        return round((total_correct / total_attempts) * 100)

    render_top_dashboard(vocab_df, mastered_vocab, total_score, accuracy_percent, st.session_state.get("current_streak", 0), total_vocab)

    mode = st.radio("Pilih mode", ["Hanzi → Arti", "Arti → Hanzi"], horizontal=True)
    if mode != st.session_state.get("quiz_mode", "Hanzi → Arti"):
        st.session_state.quiz_mode = mode
        st.session_state.quiz_options = []
        st.session_state.quiz_answered = False
        st.session_state.quiz_feedback = None
        rerun_app()

    if total_vocab == 0:
        return

    pool = build_quiz_pool(total_vocab, st.session_state.get("wrong_quiz", set()), st.session_state.get("rep_mode", "Normal"), rerun_app)
    if not pool:
        return

    idx = st.session_state.get("quiz_idx", 0) % len(pool)
    question_idx = pool[idx]
    item = vocab_df.iloc[question_idx]

    if not st.session_state.get("quiz_options"):
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
            val = vocab_df.iloc[i][candidate_col]
            if val != benar and val not in others:
                others.append(val)
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
        st.session_state.current_pinyin = item["Pinyin"]
        st.session_state.current_arti = item["Arti Indonesia"]
        st.session_state.current_contoh = item.get("Contoh", "")
        st.session_state.current_item = item

    st.progress((idx + 1) / len(pool))
    st.caption(f"Soal {idx+1} dari {len(pool)} | Streak {st.session_state.get('current_streak', 0)}")

    col_soal, col_spk = st.columns([4, 1])
    with col_soal:
        st.markdown(f"<div class='hanzi-giant'>{st.session_state.current_soal}</div>", unsafe_allow_html=True)
    with col_spk:
        render_speaker_button(st.session_state.current_soal, f"quiz_soal_{question_idx}")

    if st.button("🔊 Tampilkan Pinyin", key="quiz_pin"):
        st.session_state.quiz_show_pinyin = not st.session_state.get("quiz_show_pinyin", False)
        rerun_app()

    if st.session_state.get("quiz_show_pinyin", False):
        st.markdown(f"<div style='text-align:center'><span class='pinyin-chip'>{st.session_state.current_pinyin}</span></div>", unsafe_allow_html=True)

    if not st.session_state.get("quiz_answered", False):
        cols = st.columns(2)
        for i, opt in enumerate(st.session_state.quiz_options):
            with cols[i % 2]:
                col_btn, col_opt_spk = st.columns([4, 1])
                with col_btn:
                    if st.button(opt, key=f"quiz_{question_idx}_{i}", use_container_width=True):
                        st.session_state.quiz_answered = True
                        st.session_state.quiz_attempts = st.session_state.get("quiz_attempts", 0) + 1
                        is_correct = opt == st.session_state.current_benar
                        st.session_state.user_answer = opt
                        if is_correct:
                            st.session_state.quiz_correct_attempts = st.session_state.get("quiz_correct_attempts", 0) + 1
                            if question_idx not in st.session_state.get("quiz_answered_set", set()):
                                st.session_state.score_quiz = st.session_state.get("score_quiz", 0) + 10
                                st.session_state.quiz_answered_set.add(question_idx)
                            st.session_state.wrong_quiz.discard(question_idx)
                            st.session_state.quiz_feedback = "correct"
                        else:
                            st.session_state.wrong_quiz.add(question_idx)
                            st.session_state.quiz_feedback = "wrong"
                        # update streak
                        if is_correct:
                            st.session_state.current_streak = st.session_state.get("current_streak", 0) + 1
                            st.session_state.best_streak = max(st.session_state.get("best_streak", 0), st.session_state.current_streak)
                        else:
                            st.session_state.current_streak = 0
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
            color = "green" if st.session_state.quiz_feedback == "correct" else "red"
            st.markdown(f"<span style='color:{color}'>{user_ans}</span>", unsafe_allow_html=True)
            if st.session_state.quiz_mode == "Arti → Hanzi" and user_ans != "-":
                user_row = vocab_df[vocab_df["Kosakata"] == user_ans]
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

    st.metric("Skor Kuis", st.session_state.get("score_quiz", 0))