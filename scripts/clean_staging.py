import hashlib
import pandas as pd
from datetime import datetime
from scripts.utils.db import engine
from scripts.config import ARCHIVO_CSV, CSV_SEPARATOR


def leer_bronze():
    """
    Lee los datos crudos desde staging.amazon_sales_raw
    y parsea el JSON de raw_payload.
    """
    df_raw = pd.read_sql("SELECT * FROM staging.amazon_sales_raw", engine)
    registros = []
    for _, row in df_raw.iterrows():
        import json
        payload = json.loads(row["raw_payload"])
        payload["batch_id"] = row["batch_id"]
        payload["source_file"] = row["source_file"]
        registros.append(payload)
    df = pd.DataFrame(registros)
    print(f"Filas leidas desde Bronze: {len(df):,}")
    return df


def generar_sale_id(df):
    """
    Genera un ID unico por orden usando MD5
    de user_id + product_id + purchase_date.
    Evita duplicados en fact_orders.
    """
    def calcular_id(row):
        raw = f"{row['user_id']}_{row['product_id']}_{row['purchase_date']}"
        return hashlib.md5(raw.encode()).hexdigest()
    df["sale_id"] = df.apply(calcular_id, axis=1)
    return df


def imputar_nulos(df):
    """
    Completa valores nulos utilizando reglas
    definidas para cada columna.
    """
    df["discount"] = df["discount"].fillna(0)
    df["rating"] = df.groupby("category")["rating"].transform(
        lambda x: x.fillna(x.mean())
    )
    df["review_count"] = df["review_count"].fillna(df["review_count"].median())
    df["shipping_time_days"] = df.groupby("location")["shipping_time_days"].transform(
        lambda x: x.fillna(x.mean())
    )
    df["seller_rating"] = df["seller_rating"].fillna(df["seller_rating"].mean())
    print("Imputacion de nulos completada")
    return df


def estandarizar_texto(df):
    """
    Limpia espacios extras y estandariza mayusculas
    en columnas de texto.
    """
    columnas_texto = [
        "category", "subcategory", "brand",
        "location", "device", "payment_method",
        "delivery_status"
    ]
    for col in columnas_texto:
        df[col] = df[col].str.strip()
        df[col] = df[col].str.title()
    print("Estandarizacion de texto completada")
    return df


def convertir_tipos(df):
    """
    Convierte columnas al tipo de dato correcto
    y agrega columnas de fecha derivadas.
    """
    df["purchase_date"] = pd.to_datetime(df["purchase_date"], format="mixed")
    df["purchase_timestamp"] = df["purchase_date"]
    df["purchase_year"] = df["purchase_date"].dt.year
    df["purchase_month"] = df["purchase_date"].dt.month
    df["purchase_day"] = df["purchase_date"].dt.day
    df["is_returned"] = df["is_returned"].map({"True": True, "False": False})
    for col in ["price", "discount", "final_price", "rating",
                "review_count", "stock", "seller_rating", "shipping_time_days"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    print("Conversion de tipos completada")
    return df


def cargar_en_fact_orders(df):
    """
    Carga el dataframe en analytics.fact_orders.
    Solo inserta filas con sale_id nuevo para
    evitar duplicados históricos.
    """
    existing_ids = pd.read_sql(
        "SELECT sale_id FROM analytics.fact_orders", engine
    )
    df = df[~df["sale_id"].isin(existing_ids["sale_id"])]
    df.to_sql(
        "fact_orders",
        engine,
        schema="analytics",
        if_exists="append",
        index=False
    )
    print(f"Carga completada: {len(df):,} filas nuevas en analytics.fact_orders")


# funcion principal
def clean_staging(**context):
    """
    Lee Bronze, limpia los datos y carga en
    analytics.fact_orders (reemplaza Silver).
    """
    print("=" * 50)
    print("Inicio limpieza y carga fact_orders")
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)

    df = leer_bronze()
    df = generar_sale_id(df)
    df = imputar_nulos(df)
    df = estandarizar_texto(df)
    df = convertir_tipos(df)
    cargar_en_fact_orders(df)

    print("=" * 50)
    print("Limpieza y carga finalizada")
    print("=" * 50)


if __name__ == "__main__":
    clean_staging()