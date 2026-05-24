"""
KPI de desempeno de vendedores.

Cubre RF6. Calcula ordenes, ingresos, rating promedio de vendedor y tasa de
devolucion por seller_id. Alimenta el ranking de vendedores y permite detectar
perfiles con alto volumen pero baja calidad.
"""

from scripts.kpis.common import refresh_mart


def build_seller_performance():
    refresh_mart(
        "mart_seller_performance",
        """
        INSERT INTO analytics.mart_seller_performance
        SELECT
            CURRENT_DATE AS metric_date,
            seller_id,
            COUNT(*) AS total_orders,
            SUM(final_price) AS total_revenue,
            AVG(seller_rating) AS avg_seller_rating,
            AVG(CASE WHEN is_returned THEN 1.0 ELSE 0.0 END) * 100 AS return_rate
        FROM analytics.fact_orders
        GROUP BY seller_id
        ORDER BY total_revenue DESC
        """,
    )
