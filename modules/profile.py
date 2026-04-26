import streamlit as st
from modules.config import AVATAR_OPTIONS
from modules.utils import rerun_app


def profile_is_complete():
    return bool(str(st.session_state.get("profile_name", "")).strip() and st.session_state.get("profile_avatar", ""))


def render_profile_setup():
    st.markdown("""<div class='glass-card' style='text-align:center'><h1>Mulai Belajar HSK 3</h1><p>Isi username dan pilih avatar.</p></div>""", unsafe_allow_html=True)
    _, center, _ = st.columns([1, 1.5, 1])
    with center:
        with st.form("profile_setup_form"):
            username = st.text_input("Username", value=st.session_state.get("profile_name", ""), max_chars=24, placeholder="mis. Alex")
            current_avatar = st.session_state.get("profile_avatar", AVATAR_OPTIONS[0])
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
    st.markdown(f"""<div class="glass-soft" style="text-align:center"><div style="font-size:2rem">{st.session_state.get("profile_avatar", "😀")}</div><div style="font-weight:800">{st.session_state.get("profile_name", "")}</div><div style="font-size:0.85rem">Progress tersimpan otomatis</div></div>""", unsafe_allow_html=True)
    with st.expander("Ubah profil", expanded=False):
        with st.form("profile_sidebar_form"):
            username = st.text_input("Username", value=st.session_state.get("profile_name", ""), max_chars=24, key="profile_sidebar_name")
            current_avatar = st.session_state.get("profile_avatar", AVATAR_OPTIONS[0])
            avatar_index = AVATAR_OPTIONS.index(current_avatar) if current_avatar in AVATAR_OPTIONS else 0
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