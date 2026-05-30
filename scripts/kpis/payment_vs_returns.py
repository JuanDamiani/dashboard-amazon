"""
KPI de relacion entre metodo de pago y tasa de devolucion.
 
Cubre RF4 y RF5. Calcula ordenes totales, ordenes devueltas y tasa de
devolucion por metodo de pago. Permite identificar si ciertos metodos de
pago tienen mayor correlacion con devoluciones.
"""
 
from scripts.kpis.common import refresh_mart
 
 
def build_payment_vs_returns():
    refresh_mart(
        "mart_payment_vs_returns",
        """
        INSERT INTO analytics.mart_payment_vs_returns
        SELECT
            CURRENT_DATE AS metric_date,
            payment_method,
            COUNT(*) AS total_orders,
            SUM(CASE WHEN is_returned THEN 1 ELSE 0 END) AS returned_orders,
            ROUND(AVG(CASE WHEN is_returned THEN 1.0 ELSE 0.0 END) * 100, 2) AS return_rate
        FROM analytics.fact_orders
        GROUP BY payment_method
        ORDER BY return_rate DESC
        """,
    )
 