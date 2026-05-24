"""
Registro y control de archivos procesados.

Este modulo implementa RF14. Antes de procesar, compara nombre y hash del CSV
seleccionado contra analytics.processed_files para evitar reprocesar exactamente
el mismo archivo. Al finalizar una corrida exitosa, registra el archivo y su
batch_id.
"""

from airflow.exceptions import AirflowSkipException
from sqlalchemy import text

from scripts.config import ARCHIVO_CSV
from scripts.utils.db import engine
from scripts.utils.input_file import calculate_file_hash, get_selected_csv_path


def _ensure_processed_files_shape(conn):
    conn.execute(text("""
        ALTER TABLE analytics.processed_files
        ADD COLUMN IF NOT EXISTS file_hash VARCHAR(64)
    """))
    conn.execute(text("""
        ALTER TABLE analytics.processed_files
        DROP CONSTRAINT IF EXISTS processed_files_file_name_key
    """))
    conn.execute(text("""
        CREATE UNIQUE INDEX IF NOT EXISTS idx_processed_files_name_hash
        ON analytics.processed_files(file_name, file_hash)
    """))


def check_file_not_processed(**context):
    """Stops the DAG if the selected CSV was already processed."""
    file_path = get_selected_csv_path(context)
    file_name = file_path.name
    file_hash = context["ti"].xcom_pull(key="input_csv_hash", task_ids="check_input_file_available")
    file_hash = file_hash or calculate_file_hash(file_path)
    query = text("""
        SELECT COUNT(*) AS total
        FROM analytics.processed_files
        WHERE file_name = :file_name
          AND file_hash = :file_hash
    """)
    with engine.begin() as conn:
        _ensure_processed_files_shape(conn)
        total = conn.execute(query, {"file_name": file_name, "file_hash": file_hash}).scalar()

    if total:
        raise AirflowSkipException(f"Archivo ya procesado: {file_name}")

    print(f"Archivo pendiente de procesamiento: {file_name}")


def register_processed_file(**context):
    """Registers the processed file to avoid loading the same CSV again."""
    file_path = get_selected_csv_path(context)
    file_name = context["ti"].xcom_pull(key="input_csv_name", task_ids="check_input_file_available")
    file_name = file_name or file_path.name or ARCHIVO_CSV.name
    batch_id = context["ti"].xcom_pull(key="batch_id", task_ids="load_staging") if context.get("ti") else None
    file_hash = context["ti"].xcom_pull(key="input_csv_hash", task_ids="check_input_file_available")
    file_hash = file_hash or calculate_file_hash(file_path)

    query = text("""
        INSERT INTO analytics.processed_files (file_name, file_hash, batch_id)
        VALUES (:file_name, :file_hash, :batch_id)
        ON CONFLICT (file_name, file_hash) DO NOTHING
    """)
    with engine.begin() as conn:
        _ensure_processed_files_shape(conn)
        conn.execute(query, {"file_name": file_name, "file_hash": file_hash, "batch_id": batch_id})
    print(f"Archivo registrado: {file_name}")
