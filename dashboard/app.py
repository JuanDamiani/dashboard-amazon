import streamlit as st

st.set_page_config(
    page_title="Amazon Analytics",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="collapsed",
)

pg = st.navigation(
    [
        st.Page("pages/01_overview.py",   title="Overview",    default=True),
        st.Page("pages/02_ventas.py",     title="Ventas"),
        st.Page("pages/03_logistica.py",  title="Logística"),
        st.Page("pages/04_clientes.py",   title="Clientes"),
        st.Page("pages/05_vendedores.py", title="Vendedores"),
        st.Page("pages/06_glosario.py",   title="Glosario"),
    ],
    position="hidden",
)
pg.run()