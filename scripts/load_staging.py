import pandas as pd
from sqlalchemy import create_engine
from datetime import datetime
from scripts.load import cargar_tabla
from scripts.config import (ARCHIVO_CSV, COLUMNAS_CRITICAS,CSV_SEPARATOR)


def leer_csv():
    """
    Lee el archivo CSV y retorna el dataframe
    con los datos originales.
    """
    df = pd.read_csv(ARCHIVO_CSV, sep=CSV_SEPARATOR)
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


def cargar_en_postgresql(df):
    """
    Carga el dataframe en staging.amazon_sales_raw (Bronze).
    """
    cargar_tabla(df, "amazon_sales_raw", "staging")

# funcion principal

def load_staging():
    """
    Ejecuta el proceso de carga de datos crudos
    en la capa Bronze de staging.
    """
    print("=" * 50)
    print("Inicio carga Bronze")
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)

    df = leer_csv()
    df = eliminar_duplicados(df)
    df = eliminar_nulos_criticos(df)
    cargar_en_postgresql(df)

    print("=" * 50)
    print("Carga Bronze finalizada")
    print("=" * 50)


if __name__ == "__main__":
    load_staging()