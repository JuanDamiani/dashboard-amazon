import streamlit as st
from utils.style import get_css

st.set_page_config(
    page_title="Amazon Analytics",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(get_css(), unsafe_allow_html=True)

# ── Paginas ──────────────────────────────────────────────
PAGES = {
    "Overview":   "pages/01_overview.py",
    "Ventas":     "pages/02_ventas.py",
    "Logística":  "pages/03_logistica.py",
    "Clientes":   "pages/04_clientes.py",
    "Vendedores": "pages/05_vendedores.py",
    "Glosario":   "pages/06_glosario.py",
}

# Routing: nav nativa oculta, navegamos nosotros con el radio de abajo.
pg = st.navigation(
    [st.Page(path, title=title, default=(title == "Overview"))
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

st.markdown('<hr style="margin:0 0 8px 0;border-color:#E4E9F0;">',
            unsafe_allow_html=True)

# ── Renderiza la pagina actual ───────────────────────────
pg.run()