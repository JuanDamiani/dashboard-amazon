"""
Validacion del archivo CSV de entrada.

Este script implementa RF11 del SRS: antes de iniciar el procesamiento, revisa
que el archivo tenga las columnas requeridas, tipos numericos validos, fechas
parseables, valores permitidos y rangos razonables. Si encuentra errores
criticos, falla la tarea de Airflow para que no se carguen datos invalidos.
"""

import pandas as pd
from datetime import datetime

from scripts.config import (
    COLUMNAS_CRITICAS,
    COLUMNAS_NUMERICAS,
    COLUMNAS_REQUERIDAS,
    VALORES_ADVERTENCIA,
    VALORES_ESTRICTOS,
)
from scripts.utils.csv_reader import read_csv_auto
from scripts.utils.input_file import get_selected_csv_path
from scripts.utils.validation_summary import record_validation_summary


def verificar_archivo(file_path):
    """Checks that the selected CSV exists and loads it as strings."""
    if not file_path.exists():
        raise FileNotFoundError(f"Archivo no encontrado: {file_path}")
    df = read_csv_auto(file_path, dtype=str)
    print(f"Archivo leido: {file_path.name} ({len(df):,} filas)")
    return df


def verificar_columnas(df, errores):
    faltantes = [col for col in COLUMNAS_REQUERIDAS if col not in df.columns]
    if faltantes:
        errores.append(f"Columnas faltantes: {faltantes}")
    return errores


def verificar_nulos(df, errores):
    for col in COLUMNAS_CRITICAS:
        nulos = df[col].isna().sum()
        if nulos > 0:
            errores.append(f"'{col}': {nulos} valores nulos")
    return errores


def verificar_numericos(df, errores):
    for col in COLUMNAS_NUMERICAS:
        no_numericos = pd.to_numeric(df[col], errors="coerce").isna().sum()
        if no_numericos > 0:
            errores.append(f"'{col}': {no_numericos} valores no numericos")
    return errores


def verificar_fechas(df, errores):
    fechas_invalidas = pd.to_datetime(
        df["purchase_date"], format="mixed", errors="coerce"
    ).isna().sum()
    if fechas_invalidas > 0:
        errores.append(f"'purchase_date': {fechas_invalidas} fechas con formato invalido")
    return errores


def verificar_valores_estrictos(df, errores):
    for col, valores_validos in VALORES_ESTRICTOS.items():
        invalidos = df[~df[col].isin(valores_validos)][col].dropna().unique().tolist()
        if invalidos:
            errores.append(f"'{col}': valores invalidos: {invalidos}")
    return errores


def verificar_valores_advertencia(df, advertencias):
    for col, valores_conocidos in VALORES_ADVERTENCIA.items():
        nuevos = df[~df[col].isin(valores_conocidos)][col].dropna().unique().tolist()
        if nuevos:
            advertencias.append(f"'{col}': valores nuevos detectados: {nuevos}")
    return advertencias


def verificar_rangos(df, errores):
    rangos = {
        "discount": (0, 100),
        "rating": (0, 5),
    }
    for col, (minimo, maximo) in rangos.items():
        valores = pd.to_numeric(df[col], errors="coerce")
        fuera_min = (valores < minimo).sum()
        fuera_max = (valores > maximo).sum()
        if fuera_min > 0:
            errores.append(f"'{col}': {fuera_min} valores menores a {minimo}")
        if fuera_max > 0:
            errores.append(f"'{col}': {fuera_max} valores mayores a {maximo}")
    return errores


def verificar_rangos_sospechosos(df, advertencias):
    rangos_sospechosos = {
        "shipping_time_days": 30,
        "stock": 10000,
        "price": 500000,
    }
    for col, limite in rangos_sospechosos.items():
        sospechosos = (pd.to_numeric(df[col], errors="coerce") > limite).sum()
        if sospechosos > 0:
            advertencias.append(f"'{col}': {sospechosos} valores mayores a {limite}")
    return advertencias


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
    errores = []
    advertencias = []

    file_path = get_selected_csv_path(context)
    df = verificar_archivo(file_path)
    total_filas = len(df)

    errores = verificar_columnas(df, errores)
    if errores:
        _mostrar_resultado(errores, advertencias, total_filas)
        record_validation_summary(file_path, total_filas, errores, advertencias)
        if context.get("ti"):
            context["ti"].xcom_push(key="validation_rows_total", value=int(total_filas))
            context["ti"].xcom_push(key="validation_error_count", value=len(errores))
            context["ti"].xcom_push(key="validation_warning_count", value=len(advertencias))
        raise ValueError("Validacion fallida: columnas faltantes")

    errores = verificar_nulos(df, errores)
    errores = verificar_numericos(df, errores)
    errores = verificar_fechas(df, errores)
    errores = verificar_valores_estrictos(df, errores)
    errores = verificar_rangos(df, errores)
    advertencias = verificar_valores_advertencia(df, advertencias)
    advertencias = verificar_rangos_sospechosos(df, advertencias)

    _mostrar_resultado(errores, advertencias, total_filas)
    record_validation_summary(file_path, total_filas, errores, advertencias)

    if errores:
        raise ValueError(f"Validacion fallida: {len(errores)} error(es) encontrado(s)")

    if context.get("ti"):
        context["ti"].xcom_push(key="validation_rows_total", value=int(total_filas))
        context["ti"].xcom_push(key="validation_error_count", value=len(errores))
        context["ti"].xcom_push(key="validation_warning_count", value=len(advertencias))

    print("Validacion exitosa")


if __name__ == "__main__":
    validate_csv()
