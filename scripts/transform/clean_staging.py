"""
Transformacion SQL y carga de la tabla de hechos.

Este script implementa RF12 y RF14. Toma el batch actual desde
staging.amazon_sales_input y deja que PostgreSQL transforme tipos, normalice
texto, genere sale_id y cargue analytics.fact_orders con ON CONFLICT DO NOTHING.
Asi se evita leer millones de filas en pandas dentro de Airflow.
"""

from datetime import datetime

from sqlalchemy import text

from scripts.utils.db import engine


def transform_batch_to_fact(batch_id):
    """Transforms the selected staging batch into analytics.fact_orders using SQL."""
    query = text("""
        WITH typed AS (
            SELECT
                md5(concat_ws('_', user_id, product_id, purchase_date)) AS sale_id,
                batch_id,
                source_file,
                CASE
                    WHEN trim(purchase_date) ~ '^[0-9]{4}-[0-9]{1,2}-[0-9]{1,2}$'
                        THEN to_date(trim(purchase_date), 'YYYY-MM-DD')
                    WHEN trim(purchase_date) ~ '^[0-9]{1,2}/[0-9]{1,2}/[0-9]{4}$'
                        THEN to_date(trim(purchase_date), 'DD/MM/YYYY')
                    ELSE NULL
                END AS purchase_date,
                user_id,
                product_id,
                seller_id,
                initcap(trim(category)) AS category,
                initcap(trim(subcategory)) AS subcategory,
                initcap(trim(brand)) AS brand,
                initcap(trim(location)) AS location,
                initcap(trim(device)) AS device,
                initcap(trim(payment_method)) AS payment_method,
                initcap(trim(delivery_status)) AS delivery_status,
                price::numeric(12,2) AS price,
                coalesce(nullif(discount, '')::numeric(5,2), 0) AS discount,
                final_price::numeric(12,2) AS final_price,
                rating::numeric(3,2) AS rating,
                review_count::integer AS review_count,
                stock::integer AS stock,
                seller_rating::numeric(3,2) AS seller_rating,
                shipping_time_days::integer AS shipping_time_days,
                CASE
                    WHEN lower(trim(is_returned)) = 'true' THEN TRUE
                    WHEN lower(trim(is_returned)) = 'false' THEN FALSE
                    ELSE NULL
                END AS is_returned
            FROM staging.amazon_sales_input
            WHERE batch_id = :batch_id
        ),
        deduped AS (
            SELECT *
            FROM (
                SELECT
                    typed.*,
                    row_number() OVER (PARTITION BY sale_id ORDER BY sale_id) AS rn
                FROM typed
            ) rows
            WHERE rn = 1
        )
        INSERT INTO analytics.fact_orders (
            sale_id,
            batch_id,
            source_file,
            purchase_timestamp,
            purchase_date,
            purchase_year,
            purchase_month,
            purchase_day,
            user_id,
            product_id,
            seller_id,
            category,
            subcategory,
            brand,
            location,
            device,
            payment_method,
            delivery_status,
            price,
            discount,
            final_price,
            rating,
            review_count,
            seller_rating,
            shipping_time_days,
            stock,
            is_returned
        )
        SELECT
            sale_id,
            batch_id,
            source_file,
            purchase_date::timestamp AS purchase_timestamp,
            purchase_date,
            extract(year from purchase_date)::integer AS purchase_year,
            extract(month from purchase_date)::integer AS purchase_month,
            extract(day from purchase_date)::integer AS purchase_day,
            user_id,
            product_id,
            seller_id,
            category,
            subcategory,
            brand,
            location,
            device,
            payment_method,
            delivery_status,
            price,
            discount,
            final_price,
            rating,
            review_count,
            seller_rating,
            shipping_time_days,
            stock,
            is_returned
        FROM deduped
        ON CONFLICT (sale_id) DO NOTHING
    """)
    with engine.begin() as conn:
        before = conn.execute(
            text("SELECT COUNT(*) FROM analytics.fact_orders")
        ).scalar()
        staging_rows = conn.execute(
            text("SELECT COUNT(*) FROM staging.amazon_sales_input WHERE batch_id = :batch_id"),
            {"batch_id": batch_id},
        ).scalar()
        conn.execute(query, {"batch_id": batch_id})
        conn.execute(text("ANALYZE analytics.fact_orders"))
        after = conn.execute(
            text("SELECT COUNT(*) FROM analytics.fact_orders")
        ).scalar()

    inserted = int(after - before)
    print(f"Filas staging del batch: {staging_rows:,}")
    print(f"Filas nuevas cargadas en fact_orders: {inserted:,}")
    return int(staging_rows), inserted


def clean_staging(**context):
    """Transforms staging rows and loads analytics.fact_orders."""
    print("=" * 50)
    print("Inicio transformacion SQL y carga fact_orders")
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)

    ti = context.get("ti")
    batch_id = ti.xcom_pull(key="batch_id", task_ids="load_staging") if ti else None
    if not batch_id:
        raise ValueError("No se encontro batch_id de load_staging")

    staging_rows, inserted = transform_batch_to_fact(batch_id)
    if ti:
        ti.xcom_push(key="fact_rows_seen", value=staging_rows)
        ti.xcom_push(key="fact_rows_loaded", value=inserted)
        ti.xcom_push(key="fact_rows_rejected", value=staging_rows - inserted)

    print("=" * 50)
    print("Transformacion y carga finalizada")
    print("=" * 50)


if __name__ == "__main__":
    clean_staging()
