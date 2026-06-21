import hmac
import os

import streamlit as st
from utils.style import get_css

st.set_page_config(
    page_title="Amazon Analytics",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(get_css(), unsafe_allow_html=True)


def _check_credentials(username, password):
    expected_user = os.getenv("DASHBOARD_AUTH_USER", "admin")
    expected_password = os.getenv("DASHBOARD_AUTH_PASSWORD", "admin")
    return (
        hmac.compare_digest(username or "", expected_user)
        and hmac.compare_digest(password or "", expected_password)
    )


def _login():
    st.markdown(
        """
        <div style="max-width:420px;margin:56px auto 18px auto;">
            <div style="font-size:1.4rem;font-weight:700;color:#1C3F5E;">Amazon Analytics</div>
            <div style="font-size:0.9rem;color:#6B7A8D;margin-top:4px;">Acceso al dashboard</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    with st.form("login_form"):
        username = st.text_input("Usuario")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Ingresar", use_container_width=True)

    if submitted:
        if _check_credentials(username, password):
            st.session_state["authenticated"] = True
            st.rerun()
        else:
            st.error("Usuario o password incorrectos.")


def _logout():
    st.session_state["authenticated"] = False
    st.rerun()


if not st.session_state.get("authenticated", False):
    _login()
    st.stop()

# ── Paginas ──────────────────────────────────────────────
PAGES = {
    "Carga":      "pages/00_carga.py",
    "Overview":   "pages/01_overview.py",
    "Ventas":     "pages/02_ventas.py",
    "Logística":  "pages/03_logistica.py",
    "Clientes":   "pages/04_clientes.py",
    "Vendedores": "pages/05_vendedores.py",
    "Glosario":   "pages/06_glosario.py",
}

# Routing: nav nativa oculta, navegamos nosotros con el radio de abajo.
pg = st.navigation(
    [st.Page(path, title=title, default=(title == "Carga"))
     for title, path in PAGES.items()],
    position="hidden",
)
current = pg.title

# ── Header: logo + pestañas (se dibuja UNA vez, en todas las paginas) ──
header_col, tabs_col = st.columns([1, 5])

with header_col:
    st.markdown(
        '<div style="padding:12px 0 0 8px;">'
        '<img src="https://upload.wikimedia.org/wikipedia/commons/a/a9/Amazon_logo.svg" '
        'style="width:90px;"/></div>',
        unsafe_allow_html=True,
    )

with tabs_col:
    tab_names = list(PAGES.keys())
    idx = tab_names.index(current) if current in tab_names else 0
    selected = st.radio(
        "nav", tab_names, horizontal=True, index=idx,
        label_visibility="collapsed",
    )
    # Si el usuario clickea otra pestaña, navegamos.
    if selected != current:
        st.switch_page(PAGES[selected])

logout_col, _ = st.columns([1, 7])
with logout_col:
    st.button("Cerrar sesion", on_click=_logout, use_container_width=True)

st.markdown('<hr style="margin:0 0 8px 0;border-color:#E4E9F0;">',
            unsafe_allow_html=True)

# ── Renderiza la pagina actual ───────────────────────────
pg.run()
