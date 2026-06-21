"""
Conexion a PostgreSQL para el dashboard Streamlit.
Lee las variables de entorno del docker-compose.

- get_engine cacheado con @st.cache_resource: UN solo motor para toda la app
  (antes se creaba uno nuevo en cada query -> lentisimo y causaba el parpadeo).
- query cacheado con @st.cache_data (TTL 5 min) por (sql, params): si los datos
  no cambiaron, no vuelve a pegarle a la base.
"""

import os
import pandas as pd
import streamlit as st
import sqlalchemy
from sqlalchemy import create_engine, text


@st.cache_resource
def get_engine():
    url = (
        f"postgresql+psycopg2://"
        f"{os.getenv('DWH_DB_USER', 'dwh')}:"
        f"{os.getenv('DWH_DB_PASSWORD', 'dwh123')}@"
        f"{os.getenv('DWH_DB_HOST', 'postgres-dwh')}:"
        f"{os.getenv('DWH_DB_PORT', '5432')}/"
        f"{os.getenv('DWH_DB_NAME', 'amazon_dwh')}"
    )
    return create_engine(url, pool_pre_ping=True)


@st.cache_data(ttl=300, show_spinner=False)
def query(sql, params=None):
    """Ejecuta una query y devuelve un DataFrame.
    Resultado cacheado por (sql, params): mismas condiciones -> sin ir a la base.
    Streamlit devuelve una copia, asi que las paginas pueden modificar el df sin
    romper el cache."""
    engine = get_engine()
    with engine.connect() as conn:
        return pd.read_sql(text(sql), conn, params=params or {})


def clear_query_cache():
    """Llamar despues de cargar datos nuevos (pagina Carga) para refrescar todo."""
    query.clear()
    get_engine.clear()