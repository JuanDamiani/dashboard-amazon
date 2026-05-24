"""
Auditoria del pipeline ETL.

Este modulo implementa parte de RF13: registra inicio, exito y fallo del
pipeline en analytics.etl_audit_log. Guarda archivo, batch, filas leidas,
filas cargadas, filas rechazadas, estado final y mensaje.
"""

from sqlalchemy import text

from scripts.config import ARCHIVO_CSV
from scripts.utils.db import engine
from scripts.utils.input_file import get_selected_csv_path


def _ensure_audit_shape(conn):
    conn.execute(text("""
        ALTER TABLE analytics.etl_audit_log
        ADD COLUMN IF NOT EXISTS rows_read INTEGER
    """))
    conn.execute(text("""
        ALTER TABLE analytics.etl_audit_log
        ADD COLUMN IF NOT EXISTS rows_loaded INTEGER
    """))
    conn.execute(text("""
        ALTER TABLE analytics.etl_audit_log
        ADD COLUMN IF NOT EXISTS rows_rejected INTEGER
    """))


def log_etl_event(
    process_name,
    status,
    message,
    rows_processed=None,
    batch_id=None,
    source_file=None,
    rows_read=None,
    rows_loaded=None,
    rows_rejected=None,
):
    query = text("""
        INSERT INTO analytics.etl_audit_log (
            process_name,
            source_file,
            batch_id,
            rows_processed,
            rows_read,
            rows_loaded,
            rows_rejected,
            status,
            message
        )
        VALUES (
            :process_name,
            :source_file,
            :batch_id,
            :rows_processed,
            :rows_read,
            :rows_loaded,
            :rows_rejected,
            :status,
            :message
        )
    """)
    with engine.begin() as conn:
        _ensure_audit_shape(conn)
        conn.execute(
            query,
            {
                "process_name": process_name,
                "source_file": source_file or ARCHIVO_CSV.name,
                "batch_id": batch_id,
                "rows_processed": rows_processed,
                "rows_read": rows_read,
                "rows_loaded": rows_loaded,
                "rows_rejected": rows_rejected,
                "status": status,
                "message": message,
            },
        )


def _xcom(ti, key, task_ids=None):
    return ti.xcom_pull(key=key, task_ids=task_ids) if ti else None


def _selected_file_name(context):
    try:
        return get_selected_csv_path(context).name
    except Exception:
        return ARCHIVO_CSV.name


def log_pipeline_start(**context):
    log_etl_event(
        "amazon_pipeline",
        "STARTED",
        "Pipeline iniciado",
        source_file=_selected_file_name(context),
    )
    print("Auditoria registrada: STARTED")


def log_pipeline_success(**context):
    ti = context.get("ti")
    batch_id = _xcom(ti, "batch_id", "load_staging")
    rows_read = _xcom(ti, "rows_read", "load_staging") or _xcom(ti, "validation_rows_total", "validate_csv")
    rows_loaded = _xcom(ti, "fact_rows_loaded", "clean_staging") or _xcom(ti, "rows_loaded", "load_staging")
    rows_rejected = _xcom(ti, "fact_rows_rejected", "clean_staging") or _xcom(ti, "rows_rejected", "load_staging")
    log_etl_event(
        "amazon_pipeline",
        "SUCCESS",
        "Pipeline finalizado correctamente",
        batch_id=batch_id,
        source_file=_selected_file_name(context),
        rows_processed=rows_loaded,
        rows_read=rows_read,
        rows_loaded=rows_loaded,
        rows_rejected=rows_rejected,
    )
    print("Auditoria registrada: SUCCESS")


def log_pipeline_failure(context):
    ti = context.get("ti")
    batch_id = _xcom(ti, "batch_id", "load_staging")
    rows_read = _xcom(ti, "rows_read", "load_staging") or _xcom(ti, "validation_rows_total", "validate_csv")
    rows_loaded = _xcom(ti, "fact_rows_loaded", "clean_staging") or _xcom(ti, "rows_loaded", "load_staging")
    rows_rejected = _xcom(ti, "fact_rows_rejected", "clean_staging") or _xcom(ti, "rows_rejected", "load_staging")
    task = context.get("task_instance")
    task_id = task.task_id if task else "unknown"
    error = context.get("exception")
    log_etl_event(
        "amazon_pipeline",
        "FAILED",
        f"Fallo en tarea {task_id}: {error}",
        batch_id=batch_id,
        source_file=_selected_file_name(context),
        rows_read=rows_read,
        rows_loaded=rows_loaded,
        rows_rejected=rows_rejected,
    )
