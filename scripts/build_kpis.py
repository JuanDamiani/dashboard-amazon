from sqlalchemy import create_engine
import pandas as pd


def build_kpis():

    engine = create_engine(
        "postgresql+psycopg2://dwh:dwh123@postgres-dwh:5432/amazon_dwh"
    )

    # =====================================================
    # KPI SALES SUMMARY
    # =====================================================

    sales_summary_query = """
    SELECT

        purchase_date::date AS metric_date,

        COUNT(*) AS total_orders,

        SUM(final_price) AS total_revenue,

        AVG(final_price) AS avg_ticket,

        AVG(rating) AS avg_product_rating,

        AVG(seller_rating) AS avg_seller_rating,

        AVG(shipping_time_days) AS avg_shipping_days,

        AVG(
            CASE
                WHEN is_returned = true THEN 1
                ELSE 0
            END
        ) * 100 AS return_rate

    FROM staging.amazon_sales_raw

    GROUP BY purchase_date::date

    ORDER BY metric_date
    """

    df_sales_summary = pd.read_sql(
        sales_summary_query,
        engine
    )

    df_sales_summary.to_sql(
        "kpi_sales_summary",
        engine,
        schema="analytics",
        if_exists="replace",
        index=False
    )

    print("KPI sales summary generado")

    # =====================================================
    # KPI TOP CATEGORIES
    # =====================================================

    category_query = """
    SELECT

        category,

        COUNT(*) AS total_orders,

        SUM(final_price) AS revenue,

        AVG(rating) AS avg_rating,

        AVG(discount) AS avg_discount

    FROM staging.amazon_sales_raw

    GROUP BY category

    ORDER BY revenue DESC
    """

    df_categories = pd.read_sql(
        category_query,
        engine
    )

    df_categories.to_sql(
        "kpi_top_categories",
        engine,
        schema="analytics",
        if_exists="replace",
        index=False
    )

    print("KPI top categories generado")

    # =====================================================
    # KPI TOP BRANDS
    # =====================================================

    brand_query = """
    SELECT

        brand,

        COUNT(*) AS total_sales,

        SUM(final_price) AS revenue,

        AVG(rating) AS avg_rating,

        AVG(seller_rating) AS avg_seller_rating

    FROM staging.amazon_sales_raw

    GROUP BY brand

    ORDER BY revenue DESC
    """

    df_brands = pd.read_sql(
        brand_query,
        engine
    )

    df_brands.to_sql(
        "kpi_top_brands",
        engine,
        schema="analytics",
        if_exists="replace",
        index=False
    )

    print("KPI top brands generado")

    # =====================================================
    # KPI DELIVERY METRICS
    # =====================================================

    delivery_query = """
    SELECT

        delivery_status,

        COUNT(*) AS total_orders,

        AVG(shipping_time_days) AS avg_shipping_days,

        AVG(
            CASE
                WHEN is_returned = true THEN 1
                ELSE 0
            END
        ) * 100 AS return_rate

    FROM staging.amazon_sales_raw

    GROUP BY delivery_status
    """

    df_delivery = pd.read_sql(
        delivery_query,
        engine
    )

    df_delivery.to_sql(
        "kpi_delivery_metrics",
        engine,
        schema="analytics",
        if_exists="replace",
        index=False
    )

    print("KPI delivery metrics generado")

    # =====================================================
    # KPI PAYMENT METHODS
    # =====================================================

    payment_query = """
    SELECT

        payment_method,

        COUNT(*) AS total_orders,

        SUM(final_price) AS revenue,

        AVG(final_price) AS avg_ticket

    FROM staging.amazon_sales_raw

    GROUP BY payment_method

    ORDER BY revenue DESC
    """

    df_payment = pd.read_sql(
        payment_query,
        engine
    )

    df_payment.to_sql(
        "kpi_payment_methods",
        engine,
        schema="analytics",
        if_exists="replace",
        index=False
    )

    print("KPI payment methods generado")

    # =====================================================
    # KPI RETURNS
    # =====================================================

    returns_query = """
    SELECT

        category,

        COUNT(*) FILTER (
            WHERE is_returned = true
        ) AS returned_orders,

        COUNT(*) AS total_orders,

        (
            COUNT(*) FILTER (
                WHERE is_returned = true
            )::numeric
            /
            COUNT(*)::numeric
        ) * 100 AS return_rate

    FROM staging.amazon_sales_raw

    GROUP BY category

    ORDER BY return_rate DESC
    """

    df_returns = pd.read_sql(
        returns_query,
        engine
    )

    df_returns.to_sql(
        "kpi_returns",
        engine,
        schema="analytics",
        if_exists="replace",
        index=False
    )

    print("KPI returns generado")

    print("Todos los KPIs fueron generados correctamente")