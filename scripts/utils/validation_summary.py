"""
Resumen persistente de validacion por archivo.

Este modulo implementa RF11 y RF13. Guarda en analytics.validation_summary el
resultado de validar cada CSV: filas revisadas, errores, advertencias y estado.
"""

from sqlalchemy import text

from scripts.utils.db import engine
from scripts.utils.input_file import calculate_file_hash


def _ensure_validation_summary_shape(conn):
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS analytics.validation_summary (
            id SERIAL PRIMARY KEY,
            file_name VARCHAR(255),
            file_hash VARCHAR(64),
            rows_total INTEGER,
            error_count INTEGER,
            warning_count INTEGER,
            status VARCHAR(50),
            errors TEXT,
            warnings TEXT,
            validated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """))


def record_validation_summary(file_path, rows_total, errores, advertencias):
    status = "FAILED" if errores else "SUCCESS"
    query = text("""
        INSERT INTO analytics.validation_summary (
            file_name,
            file_hash,
            rows_total,
            error_count,
            warning_count,
            status,
            errors,
            warnings
        )
        VALUES (
            :file_name,
            :file_hash,
            :rows_total,
            :error_count,
            :warning_count,
            :status,
            :errors,
            :warnings
        )
    """)
    with engine.begin() as conn:
        _ensure_validation_summary_shape(conn)
        conn.execute(
            query,
            {
                "file_name": file_path.name,
                "file_hash": calculate_file_hash(file_path),
                "rows_total": int(rows_total),
                "error_count": len(errores),
                "warning_count": len(advertencias),
                "status": status,
                "errors": "\n".join(errores),
                "warnings": "\n".join(advertencias),
            },
        )

