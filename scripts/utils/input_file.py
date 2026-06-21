"""
Control de disponibilidad del archivo de entrada.

Este archivo apoya RF10: el DAG puede recibir por API el nombre del CSV a
procesar o, en una ejecucion manual sin parametros, tomar un CSV pendiente de
la carpeta de entrada. Selecciona un archivo y lo pasa por XCom para que
validacion, carga y registro trabajen sobre el mismo dataset.
"""

import hashlib
from pathlib import Path

from airflow.exceptions import AirflowSkipException
from sqlalchemy import text

from scripts.config import ARCHIVO_CSV, INPUT_DIR
from scripts.utils.db import engine


def calculate_file_hash(file_path):
    digest = hashlib.sha256()
    with Path(file_path).open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def get_selected_csv_path(context):
    """Returns the CSV selected by check_input_file_available."""
    ti = context.get("ti") if context else None
    selected = ti.xcom_pull(key="input_csv_path", task_ids="check_input_file_available") if ti else None
    return Path(selected) if selected else ARCHIVO_CSV


def _requested_csv_from_conf(context):
    dag_run = context.get("dag_run") if context else None
    conf = getattr(dag_run, "conf", None) or {}
    file_name = conf.get("file_name")
    if not file_name:
        return None

    safe_name = Path(str(file_name)).name
    if safe_name != file_name:
        raise AirflowSkipException("Nombre de archivo invalido")

    if not safe_name.lower().endswith(".csv"):
        raise AirflowSkipException("El archivo indicado no es CSV")

    requested = INPUT_DIR / safe_name
    if not requested.exists():
        raise AirflowSkipException(f"Archivo solicitado no disponible: {requested}")

    return requested


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


def _is_processed(conn, file_path):
    file_path = Path(file_path)
    file_hash = calculate_file_hash(file_path)
    query = text("""
        SELECT COUNT(*) AS total
        FROM analytics.processed_files
        WHERE file_name = :file_name
          AND file_hash = :file_hash
    """)
    total = conn.execute(
        query,
        {"file_name": file_path.name, "file_hash": file_hash},
    ).scalar()
    return bool(total), file_hash


def check_input_file_available(**context):
    """Selects the requested CSV or the oldest pending CSV in INPUT_DIR."""
    input_dir = INPUT_DIR
    if not input_dir.exists():
        raise AirflowSkipException(f"Carpeta input no disponible: {input_dir}")

    requested_csv = _requested_csv_from_conf(context)
    csv_files = [requested_csv] if requested_csv else sorted(input_dir.glob("*.csv"), key=lambda path: path.stat().st_mtime)
    if not csv_files:
        raise AirflowSkipException(f"No hay archivos CSV en {input_dir}")

    with engine.begin() as conn:
        _ensure_processed_files_shape(conn)
        for csv_path in csv_files:
            processed, file_hash = _is_processed(conn, csv_path)
            if not processed:
                context["ti"].xcom_push(key="input_csv_path", value=str(csv_path))
                context["ti"].xcom_push(key="input_csv_name", value=csv_path.name)
                context["ti"].xcom_push(key="input_csv_hash", value=file_hash)
                print(f"Archivo CSV seleccionado: {csv_path}")
                return

    raise AirflowSkipException("No hay CSV pendientes de procesamiento")
