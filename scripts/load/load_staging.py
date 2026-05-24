"""
Carga Bronze del pipeline.

Este script implementa parte de RF10, RF12 y RF14. Toma el CSV validado,
elimina duplicados basicos, descarta nulos criticos y guarda cada fila original
como JSONB en staging.amazon_sales_raw. La carga se hace por chunks para poder
procesar archivos grandes sin agotar memoria en Airflow.
"""

import os
import uuid
from datetime import datetime

import pandas as pd
from sqlalchemy.dialects.postgresql import JSONB

from scripts.config import COLUMNAS_CRITICAS, COLUMNAS_REQUERIDAS
from scripts.utils.csv_reader import read_csv_auto
from scripts.utils.db import engine
from scripts.utils.input_file import get_selected_csv_path


LOAD_CHUNK_SIZE = int(os.getenv("LOAD_CHUNK_SIZE", "50000"))


def leer_csv(file_path):
    """Reads the selected CSV and returns the original dataframe."""
    df = read_csv_auto(file_path)
    print(f"Archivo leido: {file_path.name} ({len(df):,} filas)")
    return df


def iterar_csv(file_path, chunksize=LOAD_CHUNK_SIZE):
    """Reads the selected CSV in chunks to avoid loading huge files in memory."""
    return read_csv_auto(file_path, chunksize=chunksize)


def verificar_columnas_para_carga(df):
    """Fails early if load_staging receives a CSV with an invalid structure."""
    faltantes = [col for col in COLUMNAS_REQUERIDAS if col not in df.columns]
    if faltantes:
        raise ValueError(f"Columnas faltantes antes de cargar Bronze: {faltantes}")


def eliminar_duplicados(df, seen_keys=None):
    """Drops duplicated rows using the business key available in the CSV."""
    filas_antes = len(df)
    key_cols = ["user_id", "product_id", "purchase_date"]

    if seen_keys is None:
        df = df.drop_duplicates(subset=key_cols)
    else:
        local_keys = df[key_cols].astype(str).agg("|".join, axis=1)
        mask = ~local_keys.isin(seen_keys)
        df = df.loc[mask].copy()
        seen_keys.update(local_keys[mask].tolist())
        df = df.drop_duplicates(subset=key_cols)

    print(f"Duplicados eliminados: {filas_antes - len(df):,}")
    return df


def eliminar_nulos_criticos(df):
    """Drops rows with null values in critical columns."""
    filas_antes = len(df)
    df = df.dropna(subset=COLUMNAS_CRITICAS)
    print(f"Filas eliminadas por nulos criticos: {filas_antes - len(df):,}")
    return df


def convertir_a_jsonb(df, file_name, batch_id):
    """Converts CSV rows to JSONB payloads for the raw staging table."""
    raw_rows = [
        {
            "source_file": str(file_name),
            "batch_id": batch_id,
            "raw_payload": row,
        }
        for row in df.to_dict(orient="records")
    ]
    return pd.DataFrame(raw_rows)


def cargar_en_postgresql(df):
    """Appends raw rows to staging.amazon_sales_raw."""
    if df.empty:
        return 0

    df.to_sql(
        "amazon_sales_raw",
        engine,
        schema="staging",
        if_exists="append",
        index=False,
        dtype={"raw_payload": JSONB()},
        method="multi",
        chunksize=5000,
    )
    print(f"Carga completada: {len(df):,} filas en staging.amazon_sales_raw")
    return len(df)


def load_staging(**context):
    """Loads raw CSV data into the Bronze staging layer."""
    print("=" * 50)
    print("Inicio carga Bronze")
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)

    batch_id = str(uuid.uuid4())
    file_path = get_selected_csv_path(context)
    file_name = file_path.name

    total_leidas = 0
    total_cargadas = 0
    seen_keys = set()

    for chunk_number, chunk in enumerate(iterar_csv(file_path), start=1):
        if chunk_number == 1:
            verificar_columnas_para_carga(chunk)

        total_leidas += len(chunk)
        print(f"Procesando chunk {chunk_number}: {len(chunk):,} filas")

        chunk = eliminar_duplicados(chunk, seen_keys=seen_keys)
        chunk = eliminar_nulos_criticos(chunk)
        raw_chunk = convertir_a_jsonb(chunk, file_name, batch_id)
        total_cargadas += cargar_en_postgresql(raw_chunk)

    print(f"Filas leidas totales: {total_leidas:,}")
    print(f"Filas cargadas totales: {total_cargadas:,}")

    if context.get("ti"):
        context["ti"].xcom_push(key="batch_id", value=batch_id)
        context["ti"].xcom_push(key="input_csv_name", value=file_name)
        context["ti"].xcom_push(key="rows_loaded", value=total_cargadas)

    print("=" * 50)
    print("Carga Bronze finalizada")
    print("=" * 50)
    return batch_id


if __name__ == "__main__":
    load_staging()
