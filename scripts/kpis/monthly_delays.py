"""
KPI de demoras mensuales.

Cubre RF4. Calcula cantidad y porcentaje de pedidos demorados por mes. Se usa
para visualizar la tendencia mensual de demoras solicitada por el SRS.
"""

from scripts.kpis.common import refresh_mart


def build_monthly_delays():
    refresh_mart(
        "mart_demoras_mensuales",
        """
        INSERT INTO analytics.mart_demoras_mensuales
        SELECT
            CURRENT_DATE AS metric_date,
            EXTRACT(YEAR FROM purchase_date)::INTEGER AS anio,
            EXTRACT(MONTH FROM purchase_date)::INTEGER AS mes,
            SUM(CASE WHEN delivery_status = 'Delayed' THEN 1 ELSE 0 END) AS total_delayed,
            COUNT(*) AS total_orders,
            AVG(CASE WHEN delivery_status = 'Delayed' THEN 1.0 ELSE 0.0 END) * 100 AS pct_delayed
        FROM analytics.fact_orders
        GROUP BY anio, mes
        ORDER BY anio, mes
        """,
    )
