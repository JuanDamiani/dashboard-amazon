"""
KPI de ventas por categoria.

Cubre RF1 y RF3. Agrupa ordenes, ingresos, rating promedio y descuento promedio
por categoria. Sirve para graficos de distribucion de ingresos del resumen y
para el analisis detallado de ventas por categoria.
"""

from scripts.kpis.common import refresh_mart


def build_sales_by_category():
    refresh_mart(
        "mart_sales_by_category",
        """
        INSERT INTO analytics.mart_sales_by_category
        SELECT
            CURRENT_DATE AS metric_date,
            category,
            COUNT(*) AS total_orders,
            SUM(final_price) AS total_revenue,
            AVG(rating) AS avg_rating,
            AVG(discount) AS avg_discount
        FROM analytics.fact_orders
        GROUP BY category
        ORDER BY total_revenue DESC
        """,
    )
