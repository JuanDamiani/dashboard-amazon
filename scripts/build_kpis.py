import pandas as pd
from sqlalchemy import create_engine, text
from datetime import datetime
from scripts.config import DB_URL

# ============================================================
# CONEXIÓN
# ============================================================

def get_engine():
    """
    Crea y retorna la conexión a PostgreSQL.
    """
    return create_engine(DB_URL)


# ============================================================
# FUNCIONES DE CÁLCULO DE KPIs
# ============================================================

def build_sales_summary(engine):
    """
    Calcula los KPIs principales del Overview:
    total de órdenes, ingresos, ticket promedio,
    rating promedio, seller rating promedio,
    tiempo de envío promedio y tasa de devolución.
    """
    query = """
        INSERT INTO analytics.mart_sales_summary
        SELECT
            CURRENT_DATE                          AS metric_date,
            COUNT(*)                              AS total_orders,
            SUM(final_price)                      AS total_revenue,
            AVG(final_price)                      AS avg_ticket,
            AVG(rating)                           AS avg_product_rating,
            AVG(seller_rating)                    AS avg_seller_rating,
            AVG(shipping_time_days)               AS avg_shipping_days,
            AVG(CASE WHEN is_returned THEN 1.0 ELSE 0.0 END) * 100 AS return_rate
        FROM analytics.fact_orders
    """
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM analytics.mart_sales_summary"))
        conn.execute(text(query))
    print("mart_sales_summary calculado")


def build_top_categories(engine):
    """
    Calcula ingresos, órdenes, rating promedio
    y descuento promedio por categoría.
    """
    query = """
        INSERT INTO analytics.mart_sales_by_category
        SELECT
            CURRENT_DATE       AS metric_date,
            category,
            COUNT(*)            AS total_orders,
            SUM(final_price)    AS total_revenue,
            AVG(rating)         AS avg_rating,
            AVG(discount)       AS avg_discount
        FROM analytics.fact_orders
        GROUP BY category
        ORDER BY total_revenue DESC
    """
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM analytics.mart_sales_by_category"))
        conn.execute(text(query))
    print("mart_sales_by_category calculado")


def build_top_brands(engine):
    """
    Calcula ingresos, ventas, rating promedio
    y seller rating promedio por marca.
    """
    query = """
        INSERT INTO analytics.mart_sales_by_brand
        SELECT
            CURRENT_DATE       AS metric_date,
            brand,
            COUNT(*)            AS total_orders,
            SUM(final_price)    AS total_revenue,
            AVG(rating)         AS avg_rating,
            AVG(seller_rating)  AS avg_seller_rating
        FROM analytics.fact_orders
        GROUP BY brand
        ORDER BY total_revenue DESC
    """
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM analytics.mart_sales_by_brand"))
        conn.execute(text(query))
    print("mart_sales_by_brand calculado")


def build_delivery_metrics(engine):
    """
    Calcula métricas de entrega por estado:
    total de órdenes, tiempo de envío promedio
    y tasa de devolución.
    """
    query = """
        INSERT INTO analytics.mart_logistics
        SELECT
            CURRENT_DATE       AS metric_date,
            delivery_status,
            COUNT(*)                                                   AS total_orders,
            AVG(shipping_time_days)                                    AS avg_shipping_days,
            AVG(CASE WHEN is_returned THEN 1.0 ELSE 0.0 END) * 100 AS return_rate
        FROM analytics.fact_orders
        GROUP BY delivery_status
    """
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM analytics.mart_logistics"))
        conn.execute(text(query))
    print("mart_logistics calculado")


def build_payment_methods(engine):
    """
    Calcula total de órdenes, ingresos y
    ticket promedio por método de pago.
    """
    query = """
        INSERT INTO analytics.mart_payment_methods
        SELECT
            CURRENT_DATE       AS metric_date,
            payment_method,
            COUNT(*)            AS total_orders,
            SUM(final_price)    AS total_revenue,
            AVG(final_price)    AS avg_ticket
        FROM analytics.fact_orders
        GROUP BY payment_method
        ORDER BY total_revenue DESC
    """
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM analytics.mart_payment_methods"))
        conn.execute(text(query))
    print("mart_payment_methods calculado")


def build_returns(engine):
    """
    Calcula la tasa de devolución por categoría.
    """
    query = """
        INSERT INTO analytics.mart_returns
        SELECT
            CURRENT_DATE       AS metric_date,
            category,
            SUM(CASE WHEN is_returned THEN 1 ELSE 0 END)        AS returned_orders,
            COUNT(*)                                                       AS total_orders,
            AVG(CASE WHEN is_returned THEN 1.0 ELSE 0.0 END) * 100 AS return_rate
        FROM analytics.fact_orders
        GROUP BY category
        ORDER BY return_rate DESC
    """
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM analytics.mart_returns"))
        conn.execute(text(query))
    print("mart_returns calculado")


def build_ventas_mensuales(engine):
    """
    Calcula la evolución mensual de ventas:
    total de órdenes, ingresos y ticket promedio.
    """
    query = """
        INSERT INTO analytics.mart_ventas_mensuales
        SELECT
            CURRENT_DATE                       AS metric_date,
            EXTRACT(YEAR FROM purchase_date)::INTEGER    AS anio,
            EXTRACT(MONTH FROM purchase_date)::INTEGER   AS mes,
            COUNT(*)                            AS total_orders,
            SUM(final_price)                    AS revenue,
            AVG(final_price)                    AS avg_ticket
        FROM analytics.fact_orders
        GROUP BY anio, mes
        ORDER BY anio, mes
    """
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM analytics.mart_ventas_mensuales"))
        conn.execute(text(query))
    print("mart_ventas_mensuales calculado")


def build_ventas_dispositivo(engine):
    """
    Calcula la distribución de ventas por
    dispositivo y categoría.
    """
    query = """
        INSERT INTO analytics.mart_ventas_dispositivo
        SELECT
            CURRENT_DATE       AS metric_date,
            device,
            category,
            COUNT(*)            AS total_orders,
            SUM(final_price)    AS revenue
        FROM analytics.fact_orders
        GROUP BY device, category
        ORDER BY revenue DESC
    """
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM analytics.mart_ventas_dispositivo"))
        conn.execute(text(query))
    print("mart_ventas_dispositivo calculado")


def build_experiencia_cliente(engine):
    """
    Calcula rating promedio, tasa de devolución
    y tiempo de envío promedio por categoría.
    """
    query = """
        INSERT INTO analytics.mart_customer_experience
        SELECT
            CURRENT_DATE       AS metric_date,
            category,
            AVG(rating)                                                    AS avg_rating,
            AVG(CASE WHEN is_returned THEN 1.0 ELSE 0.0 END) * 100 AS return_rate,
            AVG(shipping_time_days)                                        AS avg_shipping_days
        FROM analytics.fact_orders
        GROUP BY category
        ORDER BY avg_rating DESC
    """
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM analytics.mart_customer_experience"))
        conn.execute(text(query))
    print("mart_customer_experience calculado")


def build_satisfaccion_ciudad(engine):
    """
    Calcula rating promedio, total de órdenes
    y tasa de devolución por ciudad.
    """
    query = """
        INSERT INTO analytics.mart_satisfaccion_ciudad
        SELECT
            CURRENT_DATE       AS metric_date,
            location,
            AVG(rating)                                                    AS avg_rating,
            COUNT(*)                                                       AS total_orders,
            AVG(CASE WHEN is_returned THEN 1.0 ELSE 0.0 END) * 100 AS return_rate
        FROM analytics.fact_orders
        GROUP BY location
        ORDER BY avg_rating DESC
    """
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM analytics.mart_satisfaccion_ciudad"))
        conn.execute(text(query))
    print("mart_satisfaccion_ciudad calculado")


def build_vendedores(engine):
    """
    Calcula ranking de vendedores por ingresos,
    rating promedio y tasa de devolución.
    """
    query = """
        INSERT INTO analytics.mart_seller_performance
        SELECT
            CURRENT_DATE       AS metric_date,
            seller_id,
            COUNT(*)                                                       AS total_orders,
            SUM(final_price)                                               AS total_revenue,
            AVG(seller_rating)                                             AS avg_seller_rating,
            AVG(CASE WHEN is_returned THEN 1.0 ELSE 0.0 END) * 100 AS return_rate
        FROM analytics.fact_orders
        GROUP BY seller_id
        ORDER BY total_revenue DESC
    """
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM analytics.mart_seller_performance"))
        conn.execute(text(query))
    print("mart_seller_performance calculado")


def build_logistica_ciudad(engine):
    """
    Calcula tiempo de envío promedio y tasa
    de devolución por ciudad.
    """
    query = """
        INSERT INTO analytics.mart_logistica_ciudad
        SELECT
            CURRENT_DATE       AS metric_date,
            location,
            AVG(shipping_time_days)                                        AS avg_shipping_days,
            AVG(CASE WHEN is_returned THEN 1.0 ELSE 0.0 END) * 100 AS return_rate,
            COUNT(*)                                                       AS total_orders
        FROM analytics.fact_orders
        GROUP BY location
        ORDER BY avg_shipping_days DESC
    """
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM analytics.mart_logistica_ciudad"))
        conn.execute(text(query))
    print("mart_logistica_ciudad calculado")


def build_demoras_mensuales(engine):
    """
    Calcula la tendencia mensual de pedidos
    demorados como porcentaje del total.
    """
    query = """
        INSERT INTO analytics.mart_demoras_mensuales
        SELECT
            CURRENT_DATE                                                    AS metric_date,
            EXTRACT(YEAR FROM purchase_date)::INTEGER                           AS anio,
            EXTRACT(MONTH FROM purchase_date)::INTEGER                          AS mes,
            SUM(CASE WHEN delivery_status = 'Delayed' THEN 1 ELSE 0 END)       AS total_delayed,
            COUNT(*)                                                            AS total_orders,
            AVG(CASE WHEN delivery_status = 'Delayed' THEN 1.0 ELSE 0.0 END) * 100 AS pct_delayed
        FROM analytics.fact_orders
        GROUP BY anio, mes
        ORDER BY anio, mes
    """
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM analytics.mart_demoras_mensuales"))
        conn.execute(text(query))
    print("mart_demoras_mensuales calculado")


# ============================================================
# FUNCIÓN PRINCIPAL
# ============================================================

def build_kpis():
    """
    Función principal que orquesta el cálculo
    de todos los KPIs del dashboard.
    """
    print("=" * 50)
    print("Inicio build KPIs")
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)

    engine = get_engine()

    build_sales_summary(engine)
    build_top_categories(engine)
    build_top_brands(engine)
    build_delivery_metrics(engine)
    build_payment_methods(engine)
    build_returns(engine)
    build_ventas_mensuales(engine)
    build_ventas_dispositivo(engine)
    build_experiencia_cliente(engine)
    build_satisfaccion_ciudad(engine)
    build_vendedores(engine)
    build_logistica_ciudad(engine)
    build_demoras_mensuales(engine)

    print("=" * 50)
    print("Build KPIs finalizado")
    print("=" * 50)


if __name__ == "__main__":
    build_kpis()
