"""
KPI de variacion contra periodo anterior.

Cubre RF1 y RF3. Calcula metricas mensuales y su variacion porcentual frente al
mes anterior: ordenes, ingresos, ticket promedio, tasa de devolucion y rating
promedio. Permite mostrar en el dashboard los cambios porcentuales pedidos por
el SRS.
"""

from sqlalchemy import text

from scripts.kpis.common import refresh_mart
from scripts.utils.db import engine


def build_period_variation():
    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS analytics.mart_period_variation (
                metric_date DATE,
                period_month DATE,
                total_orders INTEGER,
                total_revenue NUMERIC(14,2),
                avg_ticket NUMERIC(14,2),
                return_rate NUMERIC(6,2),
                avg_product_rating NUMERIC(4,2),
                total_orders_pct_change NUMERIC(14,4),
                total_revenue_pct_change NUMERIC(14,4),
                avg_ticket_pct_change NUMERIC(14,4),
                return_rate_pct_change NUMERIC(14,4),
                avg_product_rating_pct_change NUMERIC(14,4)
            )
        """))

    refresh_mart(
        "mart_period_variation",
        """
        INSERT INTO analytics.mart_period_variation
        WITH monthly AS (
            SELECT
                date_trunc('month', purchase_date)::date AS period_month,
                COUNT(*) AS total_orders,
                SUM(final_price) AS total_revenue,
                AVG(final_price) AS avg_ticket,
                AVG(CASE WHEN is_returned THEN 1.0 ELSE 0.0 END) * 100 AS return_rate,
                AVG(rating) AS avg_product_rating
            FROM analytics.fact_orders
            GROUP BY date_trunc('month', purchase_date)::date
        ),
        compared AS (
            SELECT
                period_month,
                total_orders,
                total_revenue,
                avg_ticket,
                return_rate,
                avg_product_rating,
                LAG(total_orders) OVER (ORDER BY period_month) AS previous_total_orders,
                LAG(total_revenue) OVER (ORDER BY period_month) AS previous_total_revenue,
                LAG(avg_ticket) OVER (ORDER BY period_month) AS previous_avg_ticket,
                LAG(return_rate) OVER (ORDER BY period_month) AS previous_return_rate,
                LAG(avg_product_rating) OVER (ORDER BY period_month) AS previous_avg_product_rating
            FROM monthly
        )
        SELECT
            CURRENT_DATE AS metric_date,
            period_month,
            total_orders,
            total_revenue,
            avg_ticket,
            return_rate,
            avg_product_rating,
            CASE
                WHEN previous_total_orders IS NULL OR previous_total_orders = 0 THEN NULL
                ELSE ((total_orders - previous_total_orders)::numeric / previous_total_orders) * 100
            END AS total_orders_pct_change,
            CASE
                WHEN previous_total_revenue IS NULL OR previous_total_revenue = 0 THEN NULL
                ELSE ((total_revenue - previous_total_revenue) / previous_total_revenue) * 100
            END AS total_revenue_pct_change,
            CASE
                WHEN previous_avg_ticket IS NULL OR previous_avg_ticket = 0 THEN NULL
                ELSE ((avg_ticket - previous_avg_ticket) / previous_avg_ticket) * 100
            END AS avg_ticket_pct_change,
            CASE
                WHEN previous_return_rate IS NULL OR previous_return_rate = 0 THEN NULL
                ELSE ((return_rate - previous_return_rate) / previous_return_rate) * 100
            END AS return_rate_pct_change,
            CASE
                WHEN previous_avg_product_rating IS NULL OR previous_avg_product_rating = 0 THEN NULL
                ELSE ((avg_product_rating - previous_avg_product_rating) / previous_avg_product_rating) * 100
            END AS avg_product_rating_pct_change
        FROM compared
        ORDER BY period_month
        """,
    )
