"""
Validacion del archivo CSV de entrada.

Este script implementa RF11 del SRS. Para soportar archivos grandes, valida por
chunks: revisa columnas, nulos criticos, numericos, fechas, valores permitidos y
rangos sin cargar todo el CSV completo en memoria.
"""

from datetime import datetime

import pandas as pd

from scripts.config import (
    COLUMNAS_CRITICAS,
    COLUMNAS_NUMERICAS,
    COLUMNAS_REQUERIDAS,
    VALORES_ADVERTENCIA,
    VALORES_ESTRICTOS,
)
from scripts.load.load_staging import LOAD_CHUNK_SIZE
from scripts.utils.csv_reader import read_csv_auto
from scripts.utils.input_file import get_selected_csv_path
from scripts.utils.validation_summary import record_validation_summary


MAX_DETALLES = 10


def _agregar_error(contadores, clave, cantidad, detalle=None):
    if cantidad <= 0:
        return
    item = contadores.setdefault(clave, {"cantidad": 0, "detalles": set()})
    item["cantidad"] += int(cantidad)
    if detalle is not None and len(item["detalles"]) < MAX_DETALLES:
        if isinstance(detalle, list):
            item["detalles"].update(str(valor) for valor in detalle[:MAX_DETALLES])
        else:
            item["detalles"].add(str(detalle))


def _formatear_resultados(contadores):
    resultados = []
    for clave, data in contadores.items():
        detalles = sorted(data["detalles"])
        detalle_txt = f" Detalles: {detalles}" if detalles else ""
        resultados.append(f"{clave}: {data['cantidad']} ocurrencia(s).{detalle_txt}")
    return resultados


def _validar_columnas(df):
    faltantes = [col for col in COLUMNAS_REQUERIDAS if col not in df.columns]
    if faltantes:
        return [f"Columnas faltantes: {faltantes}"]
    return []


def _validar_chunk(df, errores, advertencias):
    for col in COLUMNAS_CRITICAS:
        nulos = df[col].isna().sum()
        _agregar_error(errores, f"'{col}' valores nulos", nulos)

    for col in COLUMNAS_NUMERICAS:
        valores = df[col]
        no_numericos = pd.to_numeric(valores, errors="coerce").isna().sum()
        _agregar_error(errores, f"'{col}' valores no numericos", no_numericos)

    fechas_invalidas = pd.to_datetime(df["purchase_date"], format="mixed", errors="coerce").isna().sum()
    _agregar_error(errores, "'purchase_date' fechas con formato invalido", fechas_invalidas)

    for col, valores_validos in VALORES_ESTRICTOS.items():
        invalidos = df[~df[col].isin(valores_validos)][col].dropna().unique().tolist()
        _agregar_error(errores, f"'{col}' valores invalidos", len(invalidos), invalidos)

    rangos = {
        "discount": (0, 100),
        "rating": (0, 5),
    }
    for col, (minimo, maximo) in rangos.items():
        valores = pd.to_numeric(df[col], errors="coerce")
        _agregar_error(errores, f"'{col}' valores menores a {minimo}", (valores < minimo).sum())
        _agregar_error(errores, f"'{col}' valores mayores a {maximo}", (valores > maximo).sum())

    for col, valores_conocidos in VALORES_ADVERTENCIA.items():
        nuevos = df[~df[col].isin(valores_conocidos)][col].dropna().unique().tolist()
        _agregar_error(advertencias, f"'{col}' valores nuevos detectados", len(nuevos), nuevos)

    rangos_sospechosos = {
        "shipping_time_days": 30,
        "stock": 10000,
        "price": 500000,
    }
    for col, limite in rangos_sospechosos.items():
        sospechosos = (pd.to_numeric(df[col], errors="coerce") > limite).sum()
        _agregar_error(advertencias, f"'{col}' valores mayores a {limite}", sospechosos)


def _mostrar_resultado(errores, advertencias, total_filas):
    print("=" * 50)
    print("Reporte de validacion")
    print("=" * 50)
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Total filas: {total_filas:,}")
    print()

    if errores:
        print(f"Errores ({len(errores)}):")
        for error in errores:
            print(f" {error}")
    else:
        print("Sin errores")

    print()

    if advertencias:
        print(f"Advertencias ({len(advertencias)}):")
        for advertencia in advertencias:
            print(f" {advertencia}")
    else:
        print("Sin advertencias")

    print()
    print("Resultado: Validacion fallida" if errores else "Resultado: Validacion exitosa")
    print("=" * 50)


def validate_csv(**context):
    """Runs all CSV checks and fails the Airflow task on critical errors."""
    file_path = get_selected_csv_path(context)
    if not file_path.exists():
        raise FileNotFoundError(f"Archivo no encontrado: {file_path}")

    errores = {}
    advertencias = {}
    total_filas = 0

    reader = read_csv_auto(file_path, dtype=str, chunksize=LOAD_CHUNK_SIZE)
    try:
        for chunk_number, chunk in enumerate(reader, start=1):
            if chunk_number == 1:
                errores_columnas = _validar_columnas(chunk)
                if errores_columnas:
                    _mostrar_resultado(errores_columnas, [], len(chunk))
                    record_validation_summary(file_path, len(chunk), errores_columnas, [])
                    raise ValueError("Validacion fallida: columnas faltantes")

            total_filas += len(chunk)
            print(f"Validando chunk {chunk_number}: {len(chunk):,} filas")
            _validar_chunk(chunk, errores, advertencias)
    finally:
        close = getattr(reader, "close", None)
        if close:
            close()

    errores_list = _formatear_resultados(errores)
    advertencias_list = _formatear_resultados(advertencias)
    _mostrar_resultado(errores_list, advertencias_list, total_filas)
    record_validation_summary(file_path, total_filas, errores_list, advertencias_list)

    ti = context.get("ti")
    if ti:
        ti.xcom_push(key="validation_rows_total", value=int(total_filas))
        ti.xcom_push(key="validation_error_count", value=len(errores_list))
        ti.xcom_push(key="validation_warning_count", value=len(advertencias_list))

    if errores_list:
        raise ValueError(f"Validacion fallida: {len(errores_list)} error(es) encontrado(s)")

    print("Validacion exitosa")


if __name__ == "__main__":
    validate_csv()
