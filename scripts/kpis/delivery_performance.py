"""
KPI de performance de entregas.
 
Cubre RF4. Calcula porcentaje de entregas a tiempo, porcentaje de pedidos
demorados, porcentaje de pedidos en transito y porcentaje de devueltos por
estado de entrega. Permite mostrar los indicadores logisticos clave pedidos
por el SRS como escalares y como distribucion por estado.
"""
 
from scripts.kpis.common import refresh_mart
 
 
def build_delivery_performance():
    refresh_mart(
        "mart_delivery_performance",
        """
        INSERT INTO analytics.mart_delivery_performance
        SELECT
            CURRENT_DATE AS metric_date,
            COUNT(*) AS total_orders,
            SUM(CASE WHEN delivery_status = 'Delivered'  THEN 1 ELSE 0 END) AS delivered_orders,
            SUM(CASE WHEN delivery_status = 'Delayed'    THEN 1 ELSE 0 END) AS delayed_orders,
            SUM(CASE WHEN delivery_status = 'In Transit' THEN 1 ELSE 0 END) AS in_transit_orders,
            SUM(CASE WHEN delivery_status = 'Returned'   THEN 1 ELSE 0 END) AS returned_orders,
            ROUND(AVG(CASE WHEN delivery_status = 'Delivered'  THEN 1.0 ELSE 0.0 END) * 100, 2) AS pct_on_time,
            ROUND(AVG(CASE WHEN delivery_status = 'Delayed'    THEN 1.0 ELSE 0.0 END) * 100, 2) AS pct_delayed,
            ROUND(AVG(CASE WHEN delivery_status = 'In Transit' THEN 1.0 ELSE 0.0 END) * 100, 2) AS pct_in_transit,
            ROUND(AVG(CASE WHEN delivery_status = 'Returned'   THEN 1.0 ELSE 0.0 END) * 100, 2) AS pct_returned
        FROM analytics.fact_orders
        """,
    )