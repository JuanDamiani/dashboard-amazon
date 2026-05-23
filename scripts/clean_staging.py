import pandas as pd
from sqlalchemy import create_engine
from datetime import datetime
from scripts.config import (
    COLUMNAS_CRITICAS,
    DB_URL
)


def leer_bronze():
    """
    Lee los datos crudos desde staging.amazon_sales_raw
    (capa Bronze) para procesarlos.
    """
    engine = create_engine(DB_URL)
    df = pd.read_sql("SELECT * FROM staging.amazon_sales_raw", engine)
    print(f"Filas leidas desde Bronze: {len(df):,}")
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
    en columnas de texto para evitar inconsistencias.
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
    Convierte columnas al tipo de dato
    correspondiente para su procesamiento.
    """
    df["purchase_date"] = pd.to_datetime(df["purchase_date"], format="mixed")

    df["is_returned"] = df["is_returned"].map({"True": True, "False": False})

    for col in ["price", "discount", "final_price", "rating",
                "review_count", "stock", "seller_rating", "shipping_time_days"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    print("Conversion de tipos completada")
    return df


def cargar_en_silver(df):
    """
    Carga el dataframe limpio en la tabla
    staging.amazon_sales_clean de PostgreSQL (Silver).
    """
    engine = create_engine(DB_URL)
    df.to_sql(
        "amazon_sales_clean",
        engine,
        schema="staging",
        if_exists="replace",
        index=False
    )
    print(f"Carga completada: {len(df):,} filas en staging.amazon_sales_clean")


# funcion principal

def clean_staging():
    """
    Ejecuta el proceso completo de limpieza
    y carga de datos en la capa Silver.
    """
    print("=" * 50)
    print("Inicio limpieza Silver")
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)

    df = leer_bronze()
    df = imputar_nulos(df)
    df = estandarizar_texto(df)
    df = convertir_tipos(df)
    cargar_en_silver(df)

    print("=" * 50)
    print("Limpieza Silver finalizada")
    print("=" * 50)


if __name__ == "__main__":
    clean_staging()