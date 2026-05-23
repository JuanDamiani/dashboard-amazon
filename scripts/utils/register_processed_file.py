from sqlalchemy import text
from scripts.utils.db import engine


def register_processed_file(**context):
    """
    Registra en analytics.processed_files el archivo
    que fue procesado. Evita reprocesar el mismo archivo.
    Cumple RF14 de persistencia histórica.
    """
    file_name = context["ti"].xcom_pull(key="input_csv_name") if context.get("ti") else "test"
    batch_id = context["ti"].xcom_pull(key="batch_id") if context.get("ti") else "test"

    query = text("""
        INSERT INTO analytics.processed_files (file_name, batch_id)
        VALUES (:file_name, :batch_id)
        ON CONFLICT (file_name) DO NOTHING
    """)
    with engine.begin() as conn:
        conn.execute(query, {"file_name": file_name, "batch_id": batch_id})
    print(f"Archivo registrado: {file_name}")