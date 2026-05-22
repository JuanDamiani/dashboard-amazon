import pandas as pd
from sqlalchemy import create_engine
from datetime import datetime
from scripts.config import (
    ARCHIVO_CSV,
    COLUMNAS_CRITICAS,
    DB_URL
)

# funciones de limpieza

def leer_csv():
    """
    Lee el archivo CSV y retorna el dataframe
    con los datos originales.
    """
    df = pd.read_csv(ARCHIVO_CSV)
    print(f"Filas leidas: {len(df):,}")
    return df


def eliminar_duplicados(df):
    """
    Elimina registros duplicados tomando como
    referencia user_id, product_id y purchase_date.
    """
    filas_antes = len(df)
    df.drop_duplicates(subset=["user_id", "product_id", "purchase_date"], inplace=True)
    print(f"Duplicados eliminados: {filas_antes - len(df):,}")
    return df


def eliminar_nulos_criticos(df):
    """
    Elimina filas que tengan valores nulos
    en columnas críticas.
    """
    filas_antes = len(df)
    df.dropna(subset=COLUMNAS_CRITICAS, inplace=True)
    print(f"Filas eliminadas por nulos criticos: {filas_antes - len(df):,}")
    return df


def imputar_nulos(df):
    """
    Completa valores nulos utilizando reglas
    definidas para cada columna.
    """
    # discount → 0
    df["discount"] = df["discount"].fillna(0)

    # rating → promedio por categoría
    df["rating"] = df.groupby("category")["rating"].transform(
        lambda x: x.fillna(x.mean())
    )

    # review_count → mediana general
    df["review_count"] = df["review_count"].fillna(df["review_count"].median())

    # shipping_time_days → promedio por ciudad
    df["shipping_time_days"] = df.groupby("location")["shipping_time_days"].transform(
        lambda x: x.fillna(x.mean())
    )

    # seller_rating → promedio general
    df["seller_rating"] = df["seller_rating"].fillna(df["seller_rating"].mean())

    print("Imputacion de nulos completada")
    return df


def convertir_tipos(df):
    """
    Convierte columnas al tipo de dato
    correspondiente para su procesamiento.
    """
    # Fechas
    df["purchase_date"] = pd.to_datetime(df["purchase_date"], format="%d/%m/%Y")

    # Booleano
    df["is_returned"] = df["is_returned"].map({"True": True, "False": False})

    # Numéricos
    for col in ["price", "discount", "final_price", "rating",
                "review_count", "stock", "seller_rating", "shipping_time_days"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    print("Conversion de tipos completada")
    return df


def cargar_en_postgresql(df):
    """
    Carga el dataframe procesado en la tabla
    staging.amazon_sales_raw de PostgreSQL.
    """
    engine = create_engine(DB_URL)
    df.to_sql(
        "amazon_sales_raw",
        engine,
        schema="staging",
        if_exists="replace",
        index=False
    )
    print(f"Carga completada: {len(df):,} filas en staging.amazon_sales_raw")


# =funcion principal

def load_staging():
    """
    Ejecuta el proceso completo de limpieza
    y carga de datos en la capa staging.
    """
    print("=" * 50)
    print("Inicio carga staging")
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)

    df = leer_csv()
    df = eliminar_duplicados(df)
    df = eliminar_nulos_criticos(df)
    df = imputar_nulos(df)
    df = convertir_tipos(df)
    cargar_en_postgresql(df)

    print("=" * 50)
    print("Carga staging finalizada")
    print("=" * 50)