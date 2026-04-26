import pandas as pd
import streamlit as st
import os
from modules.config import DATA_FILE
from modules.utils import get_file_signature, validate_required_columns

@st.cache_data
def load_hsk3_data():
    """Memuat data dari hsk3.xlsx"""
    if not os.path.exists(DATA_FILE):
        return None, None, None, "File hsk3.xlsx tidak ditemukan."
    try:
        vocab_df = pd.read_excel(DATA_FILE, sheet_name="Kosa_kata")
        cloze_df = pd.read_excel(DATA_FILE, sheet_name="Kalimat_kosong")
        scramble_df = pd.read_excel(DATA_FILE, sheet_name="Acak")
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
@st.cache_data
def load_exam_data(exam_file: str, sheet_names: dict):
    """Memuat data ujian dari file Excel dengan nama sheet yang dinamis"""
    try:
        if not os.path.exists(exam_file):
            return None
        result = {}
        for key, sheet_name in sheet_names.items():
            result[key] = pd.read_excel(exam_file, sheet_name=sheet_name).fillna("")
        return result
    except Exception as e:
        st.error(f"Gagal memuat data {exam_file}: {e}")
        return None