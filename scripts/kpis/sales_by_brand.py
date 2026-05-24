"""
KPI de ventas por marca.

Cubre RF3. Calcula ordenes, ingresos, rating promedio y rating promedio de
vendedor por marca. Permite comparar desempeno comercial entre marcas dentro
del dashboard de ventas.
"""

from scripts.kpis.common import refresh_mart


def build_sales_by_brand():
    refresh_mart(
        "mart_sales_by_brand",
        """
        INSERT INTO analytics.mart_sales_by_brand
        SELECT
            CURRENT_DATE AS metric_date,
            brand,
            COUNT(*) AS total_orders,
            SUM(final_price) AS total_revenue,
            AVG(rating) AS avg_rating,
            AVG(seller_rating) AS avg_seller_rating
        FROM analytics.fact_orders
        GROUP BY brand
        ORDER BY total_revenue DESC
        """,
    )
