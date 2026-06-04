"""
Conexion a PostgreSQL para el dashboard Streamlit.
Lee las variables de entorno del docker-compose.
"""

import os
import pandas as pd
import sqlalchemy
from sqlalchemy import create_engine, text


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


def query(sql, params=None):
    """Ejecuta una query y devuelve un DataFrame."""
    engine = get_engine()
    with engine.connect() as conn:
        return pd.read_sql(text(sql), conn, params=params or {})