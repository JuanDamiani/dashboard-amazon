"""
KPI de satisfaccion por ciudad.

Cubre RF5. Calcula rating promedio, cantidad de ordenes y tasa de devolucion por
location. Permite identificar diferencias geograficas en la experiencia del
cliente.
"""

from scripts.kpis.common import refresh_mart


def build_satisfaction_by_city():
    refresh_mart(
        "mart_satisfaccion_ciudad",
        """
        INSERT INTO analytics.mart_satisfaccion_ciudad
        SELECT
            CURRENT_DATE AS metric_date,
            location,
            AVG(rating) AS avg_rating,
            COUNT(*) AS total_orders,
            AVG(CASE WHEN is_returned THEN 1.0 ELSE 0.0 END) * 100 AS return_rate
        FROM analytics.fact_orders
        GROUP BY location
        ORDER BY avg_rating DESC
        """,
    )
