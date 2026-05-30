"""
KPI de relacion entre demoras en la entrega y devoluciones.
 
Cubre RF4. Calcula para cada valor de shipping_time_days la cantidad de
ordenes, ordenes devueltas y tasa de devolucion. Permite identificar si
los envios mas lentos generan mas devoluciones.
"""
 
from scripts.kpis.common import refresh_mart
 
 
def build_delays_vs_returns():
    refresh_mart(
        "mart_delays_vs_returns",
        """
        INSERT INTO analytics.mart_delays_vs_returns
        SELECT
            CURRENT_DATE AS metric_date,
            shipping_time_days,
            COUNT(*) AS total_orders,
            SUM(CASE WHEN is_returned THEN 1 ELSE 0 END) AS returned_orders,
            ROUND(AVG(CASE WHEN is_returned THEN 1.0 ELSE 0.0 END) * 100, 2) AS return_rate
        FROM analytics.fact_orders
        GROUP BY shipping_time_days
        ORDER BY shipping_time_days
        """,
    )