"""
KPI de distribucion de ratings y rating por rango.
 
Cubre RF5. Calcula la distribucion de ordenes segun su calificacion exacta
y segun rangos agrupados. Permite mostrar la distribucion de satisfaccion
del cliente pedida por el SRS.
"""
 
from scripts.kpis.common import refresh_mart
 
 
def build_rating_distribution():
    refresh_mart(
        "mart_rating_distribution",
        """
        INSERT INTO analytics.mart_rating_distribution
        SELECT
            CURRENT_DATE AS metric_date,
            rating,
            COUNT(*) AS total_orders,
            ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) AS order_share_pct
        FROM analytics.fact_orders
        WHERE rating IS NOT NULL
        GROUP BY rating
        ORDER BY rating
        """,
    )
 
    refresh_mart(
        "mart_rating_by_range",
        """
        INSERT INTO analytics.mart_rating_by_range
        SELECT
            CURRENT_DATE AS metric_date,
            CASE
                WHEN rating < 2   THEN '1.0 - 1.9 (Muy bajo)'
                WHEN rating < 3   THEN '2.0 - 2.9 (Bajo)'
                WHEN rating < 4   THEN '3.0 - 3.9 (Medio)'
                WHEN rating < 4.5 THEN '4.0 - 4.4 (Alto)'
                ELSE                   '4.5 - 5.0 (Muy alto)'
            END AS rating_range,
            COUNT(*) AS total_orders,
            ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) AS order_share_pct,
            ROUND(AVG(rating)::numeric, 2) AS avg_rating,
            ROUND(AVG(CASE WHEN is_returned THEN 1.0 ELSE 0.0 END) * 100, 2) AS return_rate
        FROM analytics.fact_orders
        WHERE rating IS NOT NULL
        GROUP BY rating_range
        ORDER BY rating_range
        """,
    )