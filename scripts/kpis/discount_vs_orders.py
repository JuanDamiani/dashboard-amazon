"""
KPI de relacion entre nivel de descuento y volumen de ordenes.
 
Cubre RF3. Agrupa ordenes por rango de descuento y calcula el volumen de
ordenes e ingresos por rango. Permite identificar si los descuentos mas
altos generan mas ventas.
"""
 
from scripts.kpis.common import refresh_mart
 
 
def build_discount_vs_orders():
    refresh_mart(
        "mart_discount_vs_orders",
        """
        INSERT INTO analytics.mart_discount_vs_orders
        SELECT
            CURRENT_DATE AS metric_date,
            CASE
                WHEN discount < 10 THEN '00-09%'
                WHEN discount < 20 THEN '10-19%'
                WHEN discount < 30 THEN '20-29%'
                WHEN discount < 40 THEN '30-39%'
                WHEN discount < 50 THEN '40-49%'
                WHEN discount < 60 THEN '50-59%'
                WHEN discount < 70 THEN '60-69%'
                WHEN discount < 80 THEN '70-79%'
                WHEN discount < 90 THEN '80-89%'
                ELSE                    '90-100%'
            END AS discount_range,
            COUNT(*) AS total_orders,
            ROUND(SUM(final_price)::numeric, 2) AS total_revenue,
            ROUND(AVG(final_price)::numeric, 2) AS avg_ticket
        FROM analytics.fact_orders
        GROUP BY discount_range
        ORDER BY discount_range
        """,
    )