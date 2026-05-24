"""
KPI de resumen ejecutivo.

Cubre RF1 del SRS. Genera analytics.mart_sales_summary con ingresos totales,
cantidad de ordenes, ticket promedio, rating promedio, rating de vendedor,
tiempo promedio de envio y tasa de devolucion. Esta tabla alimenta la primera
vista del dashboard para que el usuario vea el estado general del negocio.
"""

from scripts.kpis.common import refresh_mart


def build_sales_summary():
    refresh_mart(
        "mart_sales_summary",
        """
        INSERT INTO analytics.mart_sales_summary
        SELECT
            CURRENT_DATE AS metric_date,
            COUNT(*) AS total_orders,
            SUM(final_price) AS total_revenue,
            AVG(final_price) AS avg_ticket,
            AVG(rating) AS avg_product_rating,
            AVG(seller_rating) AS avg_seller_rating,
            AVG(shipping_time_days) AS avg_shipping_days,
            AVG(CASE WHEN is_returned THEN 1.0 ELSE 0.0 END) * 100 AS return_rate
        FROM analytics.fact_orders
        """,
    )
