"""
Controles de calidad posteriores a la carga.

Este script apoya RF12 y RF13: verifica que analytics.fact_orders tenga datos
despues del proceso ETL. Si la tabla queda vacia, falla la tarea para que el
usuario vea el problema en Airflow y en la auditoria.
"""

import pandas as pd
from scripts.utils.db import engine


def run_quality_checks(**context):
    """
    Verifica que analytics.fact_orders no esté vacía.
    Si está vacía significa que algo falló en el pipeline.
    """
    query = "SELECT COUNT(*) AS total FROM analytics.fact_orders"
    df = pd.read_sql(query, engine)
    total = int(df["total"][0])
    if total == 0:
        raise Exception("fact_orders está vacía. El pipeline falló.")
    print(f"Quality check OK. Filas en fact_orders: {total:,}")
