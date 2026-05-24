"""
Limpieza y carga de la tabla de hechos.

Este script implementa RF12 y RF14. Lee solamente el batch actual de Bronze,
normaliza tipos y textos, genera un sale_id estable, elimina duplicados y carga
analytics.fact_orders sin reemplazar informacion historica. La tabla fact_orders
es la fuente comun para todos los marts del dashboard.
"""

import hashlib
import json
from datetime import datetime

import pandas as pd

from scripts.utils.db import engine


def leer_bronze(batch_id=None):
    """Reads raw JSONB rows from staging.amazon_sales_raw."""
    if batch_id:
        query = "SELECT * FROM staging.amazon_sales_raw WHERE batch_id = %(batch_id)s"
        df_raw = pd.read_sql(query, engine, params={"batch_id": batch_id})
    else:
        df_raw = pd.read_sql("SELECT * FROM staging.amazon_sales_raw", engine)

    registros = []
    for _, row in df_raw.iterrows():
        payload = row["raw_payload"]
        if isinstance(payload, str):
            payload = json.loads(payload)
        payload["batch_id"] = row["batch_id"]
        payload["source_file"] = row["source_file"]
        registros.append(payload)
    df = pd.DataFrame(registros)
    print(f"Filas leidas desde Bronze: {len(df):,}")
    return df


def generar_sale_id(df):
    """Builds a stable order id from user, product and purchase date."""

    def calcular_id(row):
        raw = f"{row['user_id']}_{row['product_id']}_{row['purchase_date']}"
        return hashlib.md5(raw.encode()).hexdigest()

    df["sale_id"] = df.apply(calcular_id, axis=1)
    return df


def eliminar_duplicados_sale_id(df):
    """Keeps only one row per sale_id before loading the fact table."""
    filas_antes = len(df)
    df = df.drop_duplicates(subset=["sale_id"])
    print(f"Duplicados internos por sale_id eliminados: {filas_antes - len(df):,}")
    return df


def imputar_nulos(df):
    """Fills non-critical nulls using simple business rules."""
    columnas_numericas = [
        "price",
        "discount",
        "final_price",
        "rating",
        "review_count",
        "stock",
        "seller_rating",
        "shipping_time_days",
    ]
    for col in columnas_numericas:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df["discount"] = df["discount"].fillna(0)
    df["rating"] = df.groupby("category")["rating"].transform(lambda x: x.fillna(x.mean()))
    df["review_count"] = df["review_count"].fillna(df["review_count"].median())
    df["shipping_time_days"] = df.groupby("location")["shipping_time_days"].transform(
        lambda x: x.fillna(x.mean())
    )
    df["seller_rating"] = df["seller_rating"].fillna(df["seller_rating"].mean())
    print("Imputacion de nulos completada")
    return df


def estandarizar_texto(df):
    """Trims text fields and applies title case."""
    columnas_texto = [
        "category",
        "subcategory",
        "brand",
        "location",
        "device",
        "payment_method",
        "delivery_status",
    ]
    for col in columnas_texto:
        df[col] = df[col].str.strip()
        df[col] = df[col].str.title()
    print("Estandarizacion de texto completada")
    return df


def convertir_tipos(df):
    """Converts fields to the expected analytics types."""
    df["purchase_date"] = pd.to_datetime(df["purchase_date"], format="mixed")
    df["purchase_timestamp"] = df["purchase_date"]
    df["purchase_year"] = df["purchase_date"].dt.year
    df["purchase_month"] = df["purchase_date"].dt.month
    df["purchase_day"] = df["purchase_date"].dt.day
    df["is_returned"] = (
        df["is_returned"].astype(str).str.strip().str.lower().map({"true": True, "false": False})
    )
    for col in [
        "price",
        "discount",
        "final_price",
        "rating",
        "review_count",
        "stock",
        "seller_rating",
        "shipping_time_days",
    ]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    print("Conversion de tipos completada")
    return df


def cargar_en_fact_orders(df):
    """Appends only new sale_id values to analytics.fact_orders."""
    existing_ids = pd.read_sql("SELECT sale_id FROM analytics.fact_orders", engine)
    df = df[~df["sale_id"].isin(existing_ids["sale_id"])]
    if df.empty:
        print("No hay filas nuevas para cargar en analytics.fact_orders")
        return

    df.to_sql("fact_orders", engine, schema="analytics", if_exists="append", index=False)
    print(f"Carga completada: {len(df):,} filas nuevas en analytics.fact_orders")


def clean_staging(**context):
    """Cleans Bronze data and loads analytics.fact_orders."""
    print("=" * 50)
    print("Inicio limpieza y carga fact_orders")
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)

    ti = context.get("ti")
    batch_id = ti.xcom_pull(key="batch_id", task_ids="load_staging") if ti else None

    df = leer_bronze(batch_id=batch_id)
    if df.empty:
        print("No hay filas en Bronze para limpiar")
        return

    df = generar_sale_id(df)
    df = eliminar_duplicados_sale_id(df)
    df = imputar_nulos(df)
    df = estandarizar_texto(df)
    df = convertir_tipos(df)
    cargar_en_fact_orders(df)

    print("=" * 50)
    print("Limpieza y carga finalizada")
    print("=" * 50)


if __name__ == "__main__":
    clean_staging()
