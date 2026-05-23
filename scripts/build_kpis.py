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
        INSERT INTO analytics.kpi_sales_summary
        SELECT
            CURRENT_DATE                          AS metric_date,
            COUNT(*)                              AS total_orders,
            SUM(final_price)                      AS total_revenue,
            AVG(final_price)                      AS avg_ticket,
            AVG(rating)                           AS avg_product_rating,
            AVG(seller_rating)                    AS avg_seller_rating,
            AVG(shipping_time_days)               AS avg_shipping_days,
            AVG(CASE WHEN is_returned = 'true' THEN 1.0 ELSE 0.0 END) * 100 AS return_rate
        FROM staging.amazon_sales_clean
    """
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM analytics.kpi_sales_summary"))
        conn.execute(text(query))
    print("kpi_sales_summary calculado")


def build_top_categories(engine):
    """
    Calcula ingresos, órdenes, rating promedio
    y descuento promedio por categoría.
    """
    query = """
        INSERT INTO analytics.kpi_top_categories
        SELECT
            category,
            COUNT(*)            AS total_orders,
            SUM(final_price)    AS revenue,
            AVG(rating)         AS avg_rating,
            AVG(discount)       AS avg_discount
        FROM staging.amazon_sales_clean
        GROUP BY category
        ORDER BY revenue DESC
    """
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM analytics.kpi_top_categories"))
        conn.execute(text(query))
    print("kpi_top_categories calculado")


def build_top_brands(engine):
    """
    Calcula ingresos, ventas, rating promedio
    y seller rating promedio por marca.
    """
    query = """
        INSERT INTO analytics.kpi_top_brands
        SELECT
            brand,
            COUNT(*)            AS total_sales,
            SUM(final_price)    AS revenue,
            AVG(rating)         AS avg_rating,
            AVG(seller_rating)  AS avg_seller_rating
        FROM staging.amazon_sales_clean
        GROUP BY brand
        ORDER BY revenue DESC
    """
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM analytics.kpi_top_brands"))
        conn.execute(text(query))
    print("kpi_top_brands calculado")


def build_delivery_metrics(engine):
    """
    Calcula métricas de entrega por estado:
    total de órdenes, tiempo de envío promedio
    y tasa de devolución.
    """
    query = """
        INSERT INTO analytics.kpi_delivery_metrics
        SELECT
            delivery_status,
            COUNT(*)                                                   AS total_orders,
            AVG(shipping_time_days)                                    AS avg_shipping_days,
            AVG(CASE WHEN is_returned = 'true' THEN 1.0 ELSE 0.0 END) * 100 AS return_rate
        FROM staging.amazon_sales_clean
        GROUP BY delivery_status
    """
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM analytics.kpi_delivery_metrics"))
        conn.execute(text(query))
    print("kpi_delivery_metrics calculado")


def build_payment_methods(engine):
    """
    Calcula total de órdenes, ingresos y
    ticket promedio por método de pago.
    """
    query = """
        INSERT INTO analytics.kpi_payment_methods
        SELECT
            payment_method,
            COUNT(*)            AS total_orders,
            SUM(final_price)    AS revenue,
            AVG(final_price)    AS avg_ticket
        FROM staging.amazon_sales_clean
        GROUP BY payment_method
        ORDER BY revenue DESC
    """
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM analytics.kpi_payment_methods"))
        conn.execute(text(query))
    print("kpi_payment_methods calculado")


def build_returns(engine):
    """
    Calcula la tasa de devolución por categoría.
    """
    query = """
        INSERT INTO analytics.kpi_returns
        SELECT
            category,
            SUM(CASE WHEN is_returned = 'true' THEN 1 ELSE 0 END)        AS returned_orders,
            COUNT(*)                                                       AS total_orders,
            AVG(CASE WHEN is_returned = 'true' THEN 1.0 ELSE 0.0 END) * 100 AS return_rate
        FROM staging.amazon_sales_clean
        GROUP BY category
        ORDER BY return_rate DESC
    """
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM analytics.kpi_returns"))
        conn.execute(text(query))
    print("kpi_returns calculado")


def build_ventas_mensuales(engine):
    """
    Calcula la evolución mensual de ventas:
    total de órdenes, ingresos y ticket promedio.
    """
    query = """
        INSERT INTO analytics.kpi_ventas_mensuales
        SELECT
            EXTRACT(YEAR FROM purchase_date)    AS anio,
            EXTRACT(MONTH FROM purchase_date)   AS mes,
            COUNT(*)                            AS total_orders,
            SUM(final_price)                    AS revenue,
            AVG(final_price)                    AS avg_ticket
        FROM staging.amazon_sales_clean
        GROUP BY anio, mes
        ORDER BY anio, mes
    """
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM analytics.kpi_ventas_mensuales"))
        conn.execute(text(query))
    print("kpi_ventas_mensuales calculado")


def build_ventas_dispositivo(engine):
    """
    Calcula la distribución de ventas por
    dispositivo y categoría.
    """
    query = """
        INSERT INTO analytics.kpi_ventas_dispositivo
        SELECT
            device,
            category,
            COUNT(*)            AS total_orders,
            SUM(final_price)    AS revenue
        FROM staging.amazon_sales_clean
        GROUP BY device, category
        ORDER BY revenue DESC
    """
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM analytics.kpi_ventas_dispositivo"))
        conn.execute(text(query))
    print("kpi_ventas_dispositivo calculado")


def build_experiencia_cliente(engine):
    """
    Calcula rating promedio, tasa de devolución
    y tiempo de envío promedio por categoría.
    """
    query = """
        INSERT INTO analytics.kpi_experiencia_cliente
        SELECT
            category,
            AVG(rating)                                                    AS avg_rating,
            AVG(CASE WHEN is_returned = 'true' THEN 1.0 ELSE 0.0 END) * 100 AS return_rate,
            AVG(shipping_time_days)                                        AS avg_shipping_days
        FROM staging.amazon_sales_clean
        GROUP BY category
        ORDER BY avg_rating DESC
    """
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM analytics.kpi_experiencia_cliente"))
        conn.execute(text(query))
    print("kpi_experiencia_cliente calculado")


def build_satisfaccion_ciudad(engine):
    """
    Calcula rating promedio, total de órdenes
    y tasa de devolución por ciudad.
    """
    query = """
        INSERT INTO analytics.kpi_satisfaccion_ciudad
        SELECT
            location,
            AVG(rating)                                                    AS avg_rating,
            COUNT(*)                                                       AS total_orders,
            AVG(CASE WHEN is_returned = 'true' THEN 1.0 ELSE 0.0 END) * 100 AS return_rate
        FROM staging.amazon_sales_clean
        GROUP BY location
        ORDER BY avg_rating DESC
    """
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM analytics.kpi_satisfaccion_ciudad"))
        conn.execute(text(query))
    print("kpi_satisfaccion_ciudad calculado")


def build_vendedores(engine):
    """
    Calcula ranking de vendedores por ingresos,
    rating promedio y tasa de devolución.
    """
    query = """
        INSERT INTO analytics.kpi_vendedores
        SELECT
            seller_id,
            COUNT(*)                                                       AS total_orders,
            SUM(final_price)                                               AS revenue,
            AVG(rating)                                                    AS avg_rating,
            AVG(CASE WHEN is_returned = 'true' THEN 1.0 ELSE 0.0 END) * 100 AS return_rate
        FROM staging.amazon_sales_clean
        GROUP BY seller_id
        ORDER BY revenue DESC
    """
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM analytics.kpi_vendedores"))
        conn.execute(text(query))
    print("kpi_vendedores calculado")


def build_logistica_ciudad(engine):
    """
    Calcula tiempo de envío promedio y tasa
    de devolución por ciudad.
    """
    query = """
        INSERT INTO analytics.kpi_logistica_ciudad
        SELECT
            location,
            AVG(shipping_time_days)                                        AS avg_shipping_days,
            AVG(CASE WHEN is_returned = 'true' THEN 1.0 ELSE 0.0 END) * 100 AS return_rate,
            COUNT(*)                                                       AS total_orders
        FROM staging.amazon_sales_clean
        GROUP BY location
        ORDER BY avg_shipping_days DESC
    """
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM analytics.kpi_logistica_ciudad"))
        conn.execute(text(query))
    print("kpi_logistica_ciudad calculado")


def build_demoras_mensuales(engine):
    """
    Calcula la tendencia mensual de pedidos
    demorados como porcentaje del total.
    """
    query = """
        INSERT INTO analytics.kpi_demoras_mensuales
        SELECT
            EXTRACT(YEAR FROM purchase_date)                                    AS anio,
            EXTRACT(MONTH FROM purchase_date)                                   AS mes,
            SUM(CASE WHEN delivery_status = 'Delayed' THEN 1 ELSE 0 END)       AS total_delayed,
            COUNT(*)                                                            AS total_orders,
            AVG(CASE WHEN delivery_status = 'Delayed' THEN 1.0 ELSE 0.0 END) * 100 AS pct_delayed
        FROM staging.amazon_sales_clean
        GROUP BY anio, mes
        ORDER BY anio, mes
    """
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM analytics.kpi_demoras_mensuales"))
        conn.execute(text(query))
    print("kpi_demoras_mensuales calculado")


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