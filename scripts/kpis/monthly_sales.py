"""
KPI de evolucion mensual de ventas.

Cubre RF3. Resume ordenes, ingresos y ticket promedio por mes. Alimenta graficos
de tendencia para detectar crecimiento, caidas y estacionalidad de ventas.
"""

from scripts.kpis.common import refresh_mart


def build_monthly_sales():
    refresh_mart(
        "mart_ventas_mensuales",
        """
        INSERT INTO analytics.mart_ventas_mensuales
        SELECT
            CURRENT_DATE AS metric_date,
            EXTRACT(YEAR FROM purchase_date)::INTEGER AS anio,
            EXTRACT(MONTH FROM purchase_date)::INTEGER AS mes,
            COUNT(*) AS total_orders,
            SUM(final_price) AS revenue,
            AVG(final_price) AS avg_ticket
        FROM analytics.fact_orders
        GROUP BY anio, mes
        ORDER BY anio, mes
        """,
    )
