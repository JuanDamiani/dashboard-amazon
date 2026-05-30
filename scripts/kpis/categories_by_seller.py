"""
KPI de categorias comercializadas por vendedor.
 
Cubre RF6. Calcula para cada combinacion de vendedor y categoria las ordenes
totales, ingresos y tasa de devolucion. Permite identificar la distribucion
de categorias por vendedor pedida por el SRS.
"""
 
from scripts.kpis.common import refresh_mart
 
 
def build_categories_by_seller():
    refresh_mart(
        "mart_categories_by_seller",
        """
        INSERT INTO analytics.mart_categories_by_seller
        SELECT
            CURRENT_DATE AS metric_date,
            seller_id,
            category,
            COUNT(*) AS total_orders,
            ROUND(SUM(final_price)::numeric, 2) AS total_revenue,
            ROUND(AVG(CASE WHEN is_returned THEN 1.0 ELSE 0.0 END) * 100, 2) AS return_rate
        FROM analytics.fact_orders
        GROUP BY seller_id, category
        ORDER BY seller_id, total_revenue DESC
        """,
    )