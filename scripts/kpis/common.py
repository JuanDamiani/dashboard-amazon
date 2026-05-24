"""
Funciones comunes para construir marts analiticos.

Este archivo no representa un KPI por si mismo, pero apoya RNF-10 porque
centraliza la logica repetida de borrar y recalcular una tabla mart. Todos los
scripts de KPI lo usan para mantener consistencia entre RF1, RF3, RF4, RF5 y
RF6.
"""

from sqlalchemy import text

from scripts.utils.db import engine


def refresh_mart(table_name, insert_sql):
    """Rebuilds a mart table from analytics.fact_orders."""
    with engine.begin() as conn:
        conn.execute(text(f"DELETE FROM analytics.{table_name}"))
        conn.execute(text(insert_sql))
    print(f"{table_name} calculado")
