import streamlit as st
import jieba
import random
from copy import deepcopy
from modules.exam_base import HSKExam
from modules.config import APP_DIR
from modules.data_loader import load_exam_data
from modules.utils import render_speaker_button, get_audio_bytes
import os


class H31003Exam(HSKExam):
    def __init__(self):
        super().__init__(
            exam_name="H31003",
            excel_path=os.path.join(APP_DIR, "h31003.xlsx"),
            sheet_config={
                'listening': 'H31003_listening_1_10',
                'reading_41_50': 'H31003_reading_41_50',
                'reading_51_60': 'H31003_reading_51_60',
                'reading_61_70': 'H31003_reading_61_70',
                'writing_71_75': 'H31003_writing_71_75',
                'writing_76_80': 'H31003_writing_76_80',
            }
        )

    def load_data(self):
        return load_exam_data(self.excel_path, self.sheet_config)

    def build_questions(self, data):
        all_q = []

        # ========== LISTENING ==========
        for _, row in data['listening'].iterrows():
            all_q.append({
                "type": "listening",
                "id": row['no'],
                "part": 1,
                "audio_text": row['dialog'],
                "options": ['A', 'B', 'C', 'E', 'F'],
                "correct": str(row['correct']).strip().upper(),
                "image_path": str(row.get('image_path', '')).strip(),
            })

        # ========== MATCHING (41-50) ==========
        for _, row in data['reading_41_50'].iterrows():
            all_q.append({
                "type": "matching",
                "soal": str(row.get("soal", "")),
                "jawaban_benar": str(row.get("jawaban", "")),
                "arti_soal": str(row.get("arti1", "")),
                "pinyin_soal": str(row.get("pinyin1", "")),
                "arti_jawaban": str(row.get("arti2", "")),
                "pinyin_jawaban": str(row.get("pinyin2", "")),
            })

        # ========== FILLWORD (51-60) ==========
        for _, row in data['reading_51_60'].iterrows():
            all_q.append({
                "type": "fillword",
                "soal": str(row.get("soal", "")),
                "jawaban_benar": str(row.get("jawaban", "")),
                "arti_soal": str(row.get("arti", "")),
                "pinyin_soal": str(row.get("pinyin1", "")),
            })

        # ========== MC PILIHAN GANDA (61-70) ==========
        for _, row in data['reading_61_70'].iterrows():
            all_q.append({
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

        # ========== ISIAN HURUF (71-75) ==========
        for _, row in data['writing_71_75'].iterrows():
            all_q.append({
                "type": "char",
                "soal": str(row.get("soal", "")),
                "jawaban_benar": str(row.get("jawaban", "")),
                "arti_soal": str(row.get("arti", "")),
                "pinyin_soal": str(row.get("pinyin", "")),
            })

        # ========== SUSUN KALIMAT (76-80) ==========
        for _, row in data['writing_76_80'].iterrows():
            kalimat = str(row.get("soal", ""))
            tokens = [t for t in jieba.cut(kalimat) if t.strip()]
            all_q.append({
                "type": "scramble",
                "soal": kalimat,
                "soal_asli": kalimat,
                "tokens": tokens,
                "jawaban_benar": "".join(tokens).replace(" ", ""),
                "arti_soal": str(row.get("arti", "")),
                "pinyin_soal": str(row.get("pinyin", "")),
            })

        return all_q

    def render_question(self, q, global_idx, start_idx, **kwargs):
        """Menampilkan satu soal berdasarkan tipenya"""
        context = kwargs.get('context', {})
        shuffled_match_answers = context.get('shuffled_match_answers', [])
        all_fill_words = context.get('all_fill_words', [])

        if q["type"] == "listening":
            st.markdown(f"**Soal {global_idx+1}** (Bagian {q['part']})")

            # Tombol audio
            if st.button(f"🔊 Dengarkan Soal {global_idx+1}", key=f"listen_audio_{global_idx}"):
                audio_bytes = get_audio_bytes(q['audio_text'], lang='zh')
                if audio_bytes:
                    st.audio(audio_bytes, format="audio/mp3", autoplay=True)
                else:
                    st.warning("Gagal memutar audio.")

            # Dropdown pilihan
            current_ans = st.session_state[self.answers_key][global_idx]
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
            st.session_state[self.answers_key][global_idx] = selected
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

            current_ans = st.session_state[self.answers_key][global_idx]
            default_idx = shuffled_match_answers.index(current_ans) if current_ans in shuffled_match_answers else 0
            st.session_state[self.answers_key][global_idx] = st.selectbox(
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
            current_ans = st.session_state[self.answers_key][global_idx]
            default_idx = st.session_state[fill_key].index(current_ans) if current_ans in st.session_state[fill_key] else 0
            st.session_state[self.answers_key][global_idx] = st.selectbox(
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
            current_ans = st.session_state[self.answers_key][global_idx]
            default_idx = pilihan_teks.index(current_ans) if current_ans in pilihan_teks else 0
            st.session_state[self.answers_key][global_idx] = st.radio(
                f"Pilih jawaban untuk soal {global_idx+1}",
                pilihan_teks,
                index=default_idx,
                key=f"h31003_mc_{global_idx}",
                label_visibility="collapsed"
            )
            st.divider()

        elif q["type"] == "char":
            st.markdown(f"**Soal {global_idx+1}.** {q['soal']}")
            current_ans = st.session_state[self.answers_key][global_idx] or ""
            st.session_state[self.answers_key][global_idx] = st.text_input(
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
                    st.session_state[self.answers_key][global_idx] = user_answer if is_correct else None
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

    def render_review(self, q, global_idx, user_ans, correct_ans):
        """Menampilkan review jawaban"""
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