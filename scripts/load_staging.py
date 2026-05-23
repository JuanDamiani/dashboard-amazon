import json
import uuid
import pandas as pd
from datetime import datetime
from scripts.utils.db import engine
from scripts.config import ARCHIVO_CSV, CSV_SEPARATOR, COLUMNAS_CRITICAS


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


def convertir_a_jsonb(df, file_name, batch_id):
    """
    Convierte el dataframe a formato JSONB
    para cargarlo en staging.amazon_sales_raw.
    Cada fila del CSV se guarda como un objeto JSON
    en la columna raw_payload.
    """
    raw_rows = []
    for _, row in df.iterrows():
        raw_rows.append({
            "source_file": str(file_name),
            "batch_id": batch_id,
            "raw_payload": json.dumps(row.to_dict(), default=str)
        })
    return pd.DataFrame(raw_rows)


def cargar_en_postgresql(df):
    """
    Carga el dataframe en staging.amazon_sales_raw (Bronze).
    Usa append para acumular datos sin borrar los anteriores.
    """
    df.to_sql(
        "amazon_sales_raw",
        engine,
        schema="staging",
        if_exists="append",
        index=False
    )
    print(f"Carga completada: {len(df):,} filas en staging.amazon_sales_raw")


# ============================================================
# FUNCIÓN PRINCIPAL
# ============================================================

def load_staging(**context):
    """
    Ejecuta el proceso de carga de datos crudos
    en la capa Bronze de staging.
    Genera un batch_id único por ejecución para
    trazabilidad y persistencia histórica.
    """
    print("=" * 50)
    print("Inicio carga Bronze")
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)

    batch_id = str(uuid.uuid4())
    file_name = ARCHIVO_CSV.name

    df = leer_csv()
    df = eliminar_duplicados(df)
    df = eliminar_nulos_criticos(df)
    df = convertir_a_jsonb(df, file_name, batch_id)
    cargar_en_postgresql(df)

    if context.get("ti"):
        context["ti"].xcom_push(key="batch_id", value=batch_id)
        context["ti"].xcom_push(key="input_csv_name", value=file_name)

    print("=" * 50)
    print("Carga Bronze finalizada")
    print("=" * 50)
    return batch_id


if __name__ == "__main__":
    load_staging()