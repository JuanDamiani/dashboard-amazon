"""
Carga Bronze tabular del pipeline.

Este script implementa RF10, RF12 y RF14. Lee el CSV por chunks y guarda datos
en staging.amazon_sales_input con columnas reales. Esta estrategia evita JSONB
masivo en Python y permite que PostgreSQL haga las transformaciones pesadas.
"""

import os
import uuid
from io import StringIO
from datetime import datetime

from sqlalchemy import text

from scripts.config import COLUMNAS_REQUERIDAS
from scripts.utils.csv_reader import read_csv_auto
from scripts.utils.db import engine
from scripts.utils.input_file import get_selected_csv_path


LOAD_CHUNK_SIZE = int(os.getenv("LOAD_CHUNK_SIZE", "50000"))


def ensure_tabular_staging_table():
    """Creates the tabular staging table when running on an existing database."""
    columns_sql = ",\n".join(f"{column} TEXT" for column in COLUMNAS_REQUERIDAS)
    query = text(f"""
        CREATE TABLE IF NOT EXISTS staging.amazon_sales_input (
            staging_id BIGSERIAL PRIMARY KEY,
            source_file VARCHAR(255) NOT NULL,
            batch_id VARCHAR(100) NOT NULL,
            loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            {columns_sql}
        )
    """)
    with engine.begin() as conn:
        conn.execute(query)
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_input_batch
            ON staging.amazon_sales_input(batch_id)
        """))
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_input_file
            ON staging.amazon_sales_input(source_file)
        """))


def leer_csv(file_path):
    """Reads the selected CSV and returns the original dataframe."""
    df = read_csv_auto(file_path)
    print(f"Archivo leido: {file_path.name} ({len(df):,} filas)")
    return df


def iterar_csv(file_path, chunksize=LOAD_CHUNK_SIZE):
    """Reads the selected CSV in chunks to avoid loading huge files in memory."""
    return read_csv_auto(file_path, dtype=str, chunksize=chunksize)


def verificar_columnas_para_carga(df):
    """Fails early if load_staging receives a CSV with an invalid structure."""
    faltantes = [col for col in COLUMNAS_REQUERIDAS if col not in df.columns]
    if faltantes:
        raise ValueError(f"Columnas faltantes antes de cargar Bronze: {faltantes}")


def preparar_staging_tabular(df, file_name, batch_id):
    """Adds metadata columns before loading into staging.amazon_sales_input."""
    df = df[COLUMNAS_REQUERIDAS].copy()
    df.insert(0, "batch_id", batch_id)
    df.insert(0, "source_file", str(file_name))
    return df


def _copy_dataframe_to_staging(df):
    """Loads a dataframe into PostgreSQL using COPY for better throughput."""
    columns = ["source_file", "batch_id"] + COLUMNAS_REQUERIDAS
    buffer = StringIO()
    df.to_csv(buffer, index=False, header=False, na_rep="\\N")
    buffer.seek(0)

    copy_sql = f"""
        COPY staging.amazon_sales_input ({", ".join(columns)})
        FROM STDIN WITH (FORMAT CSV, NULL '\\N')
    """
    raw_connection = engine.raw_connection()
    try:
        with raw_connection.cursor() as cursor:
            cursor.copy_expert(copy_sql, buffer)
        raw_connection.commit()
    except Exception:
        raw_connection.rollback()
        raise
    finally:
        raw_connection.close()


def cargar_en_postgresql(df):
    """Appends tabular rows to staging.amazon_sales_input."""
    if df.empty:
        return 0

    _copy_dataframe_to_staging(df)
    print(f"Carga completada: {len(df):,} filas en staging.amazon_sales_input")
    return len(df)


def analyze_staging_table():
    """Updates PostgreSQL statistics after a large staging load."""
    with engine.begin() as conn:
        conn.execute(text("ANALYZE staging.amazon_sales_input"))
    print("ANALYZE ejecutado sobre staging.amazon_sales_input")


def load_staging(**context):
    """Loads CSV data into the tabular Bronze staging layer."""
    print("=" * 50)
    print("Inicio carga Bronze tabular")
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)

    batch_id = str(uuid.uuid4())
    file_path = get_selected_csv_path(context)
    file_name = file_path.name
    ti = context.get("ti")

    if ti:
        ti.xcom_push(key="batch_id", value=batch_id)
        ti.xcom_push(key="input_csv_name", value=file_name)

    total_leidas = 0
    total_cargadas = 0
    ensure_tabular_staging_table()

    for chunk_number, chunk in enumerate(iterar_csv(file_path), start=1):
        if chunk_number == 1:
            verificar_columnas_para_carga(chunk)

        total_leidas += len(chunk)
        print(f"Procesando chunk {chunk_number}: {len(chunk):,} filas")

        staging_chunk = preparar_staging_tabular(chunk, file_name, batch_id)
        total_cargadas += cargar_en_postgresql(staging_chunk)

        if ti:
            ti.xcom_push(key="rows_read", value=total_leidas)
            ti.xcom_push(key="rows_loaded", value=total_cargadas)
            ti.xcom_push(key="rows_rejected", value=total_leidas - total_cargadas)

    print(f"Filas leidas totales: {total_leidas:,}")
    print(f"Filas cargadas totales: {total_cargadas:,}")
    analyze_staging_table()

    if ti:
        ti.xcom_push(key="batch_id", value=batch_id)
        ti.xcom_push(key="input_csv_name", value=file_name)
        ti.xcom_push(key="rows_read", value=total_leidas)
        ti.xcom_push(key="rows_loaded", value=total_cargadas)
        ti.xcom_push(key="rows_rejected", value=total_leidas - total_cargadas)

    print("=" * 50)
    print("Carga Bronze tabular finalizada")
    print("=" * 50)
    return batch_id


if __name__ == "__main__":
    load_staging()
