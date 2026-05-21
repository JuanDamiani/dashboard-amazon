from pathlib import Path
import pandas as pd
from datetime import datetime
from scripts.config import (
    ARCHIVO_CSV,
    COLUMNAS_REQUERIDAS,
    COLUMNAS_CRITICAS,
    COLUMNAS_NUMERICAS,
    VALORES_ESTRICTOS,
    VALORES_ADVERTENCIA
)

# ============================================================
# funcion principal
# ============================================================

def validate_csv():
    errores = []
    advertencias = []

    # 1. Verificar que el archivo existe
    if not ARCHIVO_CSV.exists():
        raise FileNotFoundError(f"Archivo no encontrado: {ARCHIVO_CSV}")

    # 2. Leer el CSV
    df = pd.read_csv(ARCHIVO_CSV, dtype=str)
    total_filas = len(df)
    print(f"Archivo leído: {total_filas:,} filas")

    # 3. Verificar columnas
    faltantes = [c for c in COLUMNAS_REQUERIDAS if c not in df.columns]
    if faltantes:
        errores.append(f"Columnas faltantes: {faltantes}")

    if errores:
        _mostrar_resultado(errores, advertencias, total_filas)
        raise ValueError("Validación fallida: columnas faltantes")

    # 4. Verificar nulos en columnas críticas
    for col in COLUMNAS_CRITICAS:
        nulos = df[col].isna().sum()
        if nulos > 0:
            errores.append(f"'{col}': {nulos} valores nulos")

    # 5. Verificar que las columnas numericas sean int
    for col in COLUMNAS_NUMERICAS:
        no_numericos = pd.to_numeric(df[col], errors='coerce').isna().sum()
        if no_numericos > 0:
            errores.append(f"'{col}': {no_numericos} valores no numéricos")

    # 6. Verificar formato de fechas (D/M/YYYY)
    fechas_invalidas = pd.to_datetime(
        df["purchase_date"], format="%d/%m/%Y", errors='coerce'
    ).isna().sum()
    if fechas_invalidas > 0:
        errores.append(f"'purchase_date': {fechas_invalidas} fechas con formato inválido")

    # 7. Verificar valores estrictos
    for col, valores_validos in VALORES_ESTRICTOS.items():
        invalidos = df[~df[col].isin(valores_validos)][col].unique().tolist()
        if invalidos:
            errores.append(f"'{col}': valores inválidos: {invalidos}")

    # 8. Verificar valores con advertencia
    for col, valores_conocidos in VALORES_ADVERTENCIA.items():
        nuevos = df[~df[col].isin(valores_conocidos)][col].dropna().unique().tolist()
        if nuevos:
            advertencias.append(f"'{col}': valores nuevos detectados: {nuevos}")

    _mostrar_resultado(errores, advertencias, total_filas)

    if errores:
        raise ValueError(f"Validacion fallida: {len(errores)} error(es) encontrado(s)")

    print("Validacion exitosa")


# ============================================================
# Función que muestra un resumen del resultado de la validación
# ============================================================

def _mostrar_resultado(errores, advertencias, total_filas):
    print("=" * 50)
    print("Reporte de validacion")
    print("=" * 50)
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Total filas: {total_filas:,}")
    print()

    if errores:
        print(f"Errores ({len(errores)}):")
        for e in errores:
            print(f"   → {e}")
    else:
        print("Sin errores")

    print()

    if advertencias:
        print(f"Advertencias ({len(advertencias)}):")
        for a in advertencias:
            print(f"   → {a}")
    else:
        print("Sin advertencias")

    print()
    if errores:
        print("Resultado: Validacion Fallida")
    else:
        print("Resultado: Validacion Exitosa")
    print("=" * 50)