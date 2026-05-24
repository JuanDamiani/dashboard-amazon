"""
KPI de experiencia del cliente por categoria.

Cubre RF5. Calcula rating promedio, tasa de devolucion y tiempo promedio de
envio por categoria. Permite observar la relacion entre satisfaccion,
devoluciones y tiempos logisticos.
"""

from scripts.kpis.common import refresh_mart


def build_customer_experience():
    refresh_mart(
        "mart_customer_experience",
        """
        INSERT INTO analytics.mart_customer_experience
        SELECT
            CURRENT_DATE AS metric_date,
            category,
            AVG(rating) AS avg_rating,
            AVG(CASE WHEN is_returned THEN 1.0 ELSE 0.0 END) * 100 AS return_rate,
            AVG(shipping_time_days) AS avg_shipping_days
        FROM analytics.fact_orders
        GROUP BY category
        ORDER BY avg_rating DESC
        """,
    )
