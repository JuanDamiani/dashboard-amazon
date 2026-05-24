"""
KPI de devoluciones por categoria.

Cubre RF4 y RF5. Calcula cantidad de ordenes devueltas, total de ordenes y tasa
de devolucion por categoria. Sirve para analizar problemas logisticos y su
relacion con experiencia del cliente.
"""

from scripts.kpis.common import refresh_mart


def build_returns():
    refresh_mart(
        "mart_returns",
        """
        INSERT INTO analytics.mart_returns
        SELECT
            CURRENT_DATE AS metric_date,
            category,
            SUM(CASE WHEN is_returned THEN 1 ELSE 0 END) AS returned_orders,
            COUNT(*) AS total_orders,
            AVG(CASE WHEN is_returned THEN 1.0 ELSE 0.0 END) * 100 AS return_rate
        FROM analytics.fact_orders
        GROUP BY category
        ORDER BY return_rate DESC
        """,
    )
