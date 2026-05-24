"""
Auditoria del pipeline ETL.

Este modulo implementa parte de RF13: registra inicio, exito y fallo del
pipeline en analytics.etl_audit_log. Esa tabla permite supervisar el proceso de
carga y explicar que ocurrio en cada ejecucion.
"""

from sqlalchemy import text

from scripts.config import ARCHIVO_CSV
from scripts.utils.db import engine


def log_etl_event(process_name, status, message, rows_processed=None, batch_id=None, source_file=None):
    query = text("""
        INSERT INTO analytics.etl_audit_log (
            process_name,
            source_file,
            batch_id,
            rows_processed,
            status,
            message
        )
        VALUES (
            :process_name,
            :source_file,
            :batch_id,
            :rows_processed,
            :status,
            :message
        )
    """)
    with engine.begin() as conn:
        conn.execute(
            query,
            {
                "process_name": process_name,
                "source_file": source_file or ARCHIVO_CSV.name,
                "batch_id": batch_id,
                "rows_processed": rows_processed,
                "status": status,
                "message": message,
            },
        )


def log_pipeline_start(**context):
    log_etl_event("amazon_pipeline", "STARTED", "Pipeline iniciado")
    print("Auditoria registrada: STARTED")


def log_pipeline_success(**context):
    ti = context.get("ti")
    batch_id = ti.xcom_pull(key="batch_id", task_ids="load_staging") if ti else None
    log_etl_event("amazon_pipeline", "SUCCESS", "Pipeline finalizado correctamente", batch_id=batch_id)
    print("Auditoria registrada: SUCCESS")


def log_pipeline_failure(context):
    ti = context.get("ti")
    batch_id = ti.xcom_pull(key="batch_id", task_ids="load_staging") if ti else None
    task = context.get("task_instance")
    task_id = task.task_id if task else "unknown"
    error = context.get("exception")
    log_etl_event(
        "amazon_pipeline",
        "FAILED",
        f"Fallo en tarea {task_id}: {error}",
        batch_id=batch_id,
    )
