import streamlit as st
import random
import os
import re
from modules.utils import render_speaker_button, get_audio_bytes, rerun_app


class HSKExam:
    """Kelas dasar untuk semua ujian HSK (H31003, H31004, dll.)"""

    def __init__(self, exam_name, excel_path, sheet_config):
        self.exam_name = exam_name
        self.excel_path = excel_path
        self.sheet_config = sheet_config
        self.all_questions = []
        self.total_soal = 0
        self.per_page = 5
        self.state_prefix = exam_name.lower()
        self.answers_key = f"{self.state_prefix}_answers"
        self.page_key = f"{self.state_prefix}_page"
        self.reviewed_key = f"{self.state_prefix}_reviewed"
        self.finished_key = f"{self.state_prefix}_finished"
        self.score_key = f"{self.state_prefix}_score"
        self.match_shuffle_key = f"{self.state_prefix}_match_shuffle"

    def load_data(self):
        """Harus diimplementasikan oleh kelas turunan"""
        raise NotImplementedError

    def build_questions(self, data):
        """Membangun daftar semua soal dari data yang sudah dimuat"""
        raise NotImplementedError

    def render_question(self, q, global_idx, start_idx, **kwargs):
        """Menampilkan satu soal berdasarkan tipenya"""
        raise NotImplementedError

    def render_review(self, q, global_idx, user_ans, correct_ans):
        """Menampilkan review jawaban"""
        raise NotImplementedError

    def _init_session_state(self, total_soal, total_pages):
        """Inisialisasi session state untuk ujian ini"""
        if self.answers_key not in st.session_state:
            st.session_state[self.answers_key] = [None] * total_soal
        else:
            if len(st.session_state[self.answers_key]) != total_soal:
                st.session_state[self.answers_key] = [None] * total_soal

        if self.page_key not in st.session_state:
            st.session_state[self.page_key] = 0
        if self.reviewed_key not in st.session_state:
            st.session_state[self.reviewed_key] = [False] * total_pages
        if self.finished_key not in st.session_state:
            st.session_state[self.finished_key] = False
        if self.score_key not in st.session_state:
            st.session_state[self.score_key] = 0
        if self.match_shuffle_key not in st.session_state:
            st.session_state[self.match_shuffle_key] = {}

    def _reset_exam(self):
        """Reset semua state ujian"""
        for key in list(st.session_state.keys()):
            if (key.startswith(self.state_prefix) or
                key.startswith("scramble_tokens_") or
                key.startswith("scramble_order_") or
                key.startswith("show_pinyin_h31003_") or
                key.startswith("match_shuffle_") or
                key.startswith("fillword_options_")):
                st.session_state.pop(key, None)
        rerun_app()

    def run(self):
        """Menjalankan ujian (halaman, state, dll.)"""
        st.markdown(
            f"<div class='glass-card'><h2>📝 Latihan Soal HSK 3 ({self.exam_name})</h2>"
            f"<p>Kerjakan semua soal secara berurutan. Setiap halaman berisi {self.per_page} soal. "
            f"Skor akan dihitung setelah selesai.</p></div>",
            unsafe_allow_html=True
        )

        data = self.load_data()
        if data is None:
            st.warning(f"File {self.exam_name}.xlsx tidak ditemukan. Pastikan file ada di folder yang sama.")
            return

        self.all_questions = self.build_questions(data)
        self.total_soal = len(self.all_questions)
        per_page = self.per_page
        total_pages = (self.total_soal - 1) // per_page + 1

        self._init_session_state(self.total_soal, total_pages)

        # Tombol reset
        if st.button("🔄 Reset Latihan", use_container_width=True):
            self._reset_exam()

        current_page = st.session_state[self.page_key]
        if current_page >= total_pages:
            st.session_state[self.finished_key] = True

        if st.session_state[self.finished_key]:
            correct = 0
            for i, ans in enumerate(st.session_state[self.answers_key]):
                if ans is not None and ans == self.all_questions[i].get("jawaban_benar", self.all_questions[i].get("correct")):
                    correct += 1
            st.session_state[self.score_key] = correct
            st.balloons()
            st.success(f"✨ Latihan selesai! Skor Anda: {correct} dari {self.total_soal} ({correct/self.total_soal*100:.1f}%)")
            if st.button("Kerjakan Ulang", use_container_width=True):
                self._reset_exam()
            return

        start = current_page * per_page
        end = min(start + per_page, self.total_soal)
        page_soal = self.all_questions[start:end]

        st.markdown(f"### Halaman {current_page+1} dari {total_pages}")
        st.progress((current_page) / total_pages)

        # Siapkan data untuk fillword dan matching
        all_fill_words = list(set([q["jawaban_benar"] for q in self.all_questions if q["type"] == "fillword"]))
        if not all_fill_words and any(q["type"] == "fillword" for q in page_soal):
            st.error("Data untuk soal fillword kosong. Periksa file Excel.")
            return

        # Acakan jawaban matching
        match_answers_in_page = [q["jawaban_benar"] for q in page_soal if q["type"] == "matching"]
        if match_answers_in_page:
            shuffle_key = f"match_shuffle_{current_page}"
            if shuffle_key not in st.session_state[self.match_shuffle_key]:
                shuffled = match_answers_in_page.copy()
                random.shuffle(shuffled)
                st.session_state[self.match_shuffle_key][shuffle_key] = shuffled
            shuffled_match_answers = st.session_state[self.match_shuffle_key][shuffle_key]
        else:
            shuffled_match_answers = []

        # ========== TAMPILKAN GAMBAR LISTENING BERDERET ==========
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
                    # Ekstrak huruf dari nama file (misal ..._E.jpg -> "E")
                    fname = os.path.basename(item["image_path"])
                    match = re.search(r'_([A-F])\.(jpg|png|jpeg|webp)$', fname, re.IGNORECASE)
                    if match:
                        label_huruf = match.group(1)
                    else:
                        label_huruf = "?"   # fallback jika tidak ditemukan
                    st.markdown(
                        f"<div style='text-align:center; font-size:0.9rem; margin-top:5px;'>"
                        f"<strong>{label_huruf}</strong></div>",
                        unsafe_allow_html=True
                    )
            st.markdown("---")

        # ========== TAMPILKAN SOAL ==========
        if not st.session_state[self.reviewed_key][current_page]:
            for idx, q in enumerate(page_soal):
                global_idx = start + idx
                with st.container():
                    self.render_question(
                        q, global_idx, start,
                        context={
                            'shuffled_match_answers': shuffled_match_answers,
                            'all_fill_words': all_fill_words
                        }
                    )

            if st.button("✅ Cek Jawaban (Halaman Ini)", key=f"check_{current_page}", use_container_width=True):
                st.session_state[self.reviewed_key][current_page] = True
                st.rerun()

        else:
            # REVIEW MODE
            st.subheader("📋 Review Jawaban Halaman Ini")
            for idx, q in enumerate(page_soal):
                global_idx = start + idx
                user_ans = st.session_state[self.answers_key][global_idx]
                correct_ans = q.get("jawaban_benar", q.get("correct"))
                self.render_review(q, global_idx, user_ans, correct_ans)

            if st.button("➡️ Lanjut ke Halaman Berikutnya", key=f"next_{current_page}", use_container_width=True):
                if current_page + 1 < total_pages:
                    st.session_state[self.page_key] = current_page + 1
                    st.session_state[self.reviewed_key][current_page + 1] = False
                    st.rerun()
                else:
                    st.session_state[self.finished_key] = True
                    st.rerun()