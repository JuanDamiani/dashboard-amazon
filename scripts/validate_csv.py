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

# funciones de validacion

def verificar_archivo():
    """
    Verifica que el archivo CSV exista y lo carga.
    Todos los datos se leen como string para evitar
    conversiones automáticas de pandas.
    """
    if not ARCHIVO_CSV.exists():
        raise FileNotFoundError(f"Archivo no encontrado: {ARCHIVO_CSV}")
    df = pd.read_csv(ARCHIVO_CSV, dtype=str)
    print(f"Archivo leído: {len(df):,} filas")
    return df


def verificar_columnas(df, errores):
    """
    Valida que el archivo tenga todas las columnas requeridas.
    Si falta alguna, se registra un error y se detiene la validación.
    """
    faltantes = [c for c in COLUMNAS_REQUERIDAS if c not in df.columns]
    if faltantes:
        errores.append(f"Columnas faltantes: {faltantes}")
    return errores


def verificar_nulos(df, errores):
    """
    Verifica que las columnas críticas no tengan valores nulos.
    """
    for col in COLUMNAS_CRITICAS:
        nulos = df[col].isna().sum()
        if nulos > 0:
            errores.append(f"'{col}': {nulos} valores nulos")
    return errores


def verificar_numericos(df, errores):
    """
    Valida que las columnas numéricas contengan
    solo valores válidos y no texto u otros formatos incorrectos.
    """
    for col in COLUMNAS_NUMERICAS:
        no_numericos = pd.to_numeric(df[col], errors='coerce').isna().sum()
        if no_numericos > 0:
            errores.append(f"'{col}': {no_numericos} valores no numericos")
    return errores


def verificar_fechas(df, errores):
    """
    Valida que la columna purchase_date tenga el formato
    D/M/YYYY. Si una fecha no cumple ese formato,
    se registra como error.
    """
    fechas_invalidas = pd.to_datetime(
        df["purchase_date"], format="mixed", errors='coerce'
    ).isna().sum()
    if fechas_invalidas > 0:
        errores.append(f"'purchase_date': {fechas_invalidas} fechas con formato invalido")
    return errores


def verificar_valores_estrictos(df, errores):
    """
    Valida que las columnas con valores definidos contengan
    solo opciones permitidas. Si aparece un valor distinto,
    se registra un error y se detiene el procesamiento.
    """
    for col, valores_validos in VALORES_ESTRICTOS.items():
        invalidos = df[~df[col].isin(valores_validos)][col].unique().tolist()
        if invalidos:
            errores.append(f"'{col}': valores invalidos: {invalidos}")
    return errores


def verificar_valores_advertencia(df, advertencias):
    """
   Revisa si hay valores nuevos en columnas como categorías
   o métodos de pago. Si encuentra alguno, muestra una
   advertencia pero no detiene la validación.
    """
    for col, valores_conocidos in VALORES_ADVERTENCIA.items():
        nuevos = df[~df[col].isin(valores_conocidos)][col].dropna().unique().tolist()
        if nuevos:
            advertencias.append(f"'{col}': valores nuevos detectados: {nuevos}")
    return advertencias


# funcion que muestra el reporte (interna)

def _mostrar_resultado(errores, advertencias, total_filas):
    """
    Muestra un reporte con el resultado de la validacion,
    incluyendo la cantidad de filas procesadas, los errores
    encontrados y las advertencias generadas.
    """
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
        print("Resultado: Validacion fallida")
    else:
        print("Resultado: Validacion exitosa")
    print("=" * 50)


# funcion principal

def validate_csv():
    """
      Ejecuta las validaciones del archivo CSV y consolida los resultados.
      Si se encuentran errores críticos, se interrumpe la ejecución
      mediante una excepción para marcar la tarea como fallida en Airflow.
   """
    
    errores = []
    advertencias = []

    df = verificar_archivo()
    total_filas = len(df)

    errores = verificar_columnas(df, errores)
    if errores:
        _mostrar_resultado(errores, advertencias, total_filas)
        raise ValueError("Validación fallida: columnas faltantes")

    errores = verificar_nulos(df, errores)
    errores = verificar_numericos(df, errores)
    errores = verificar_fechas(df, errores)
    errores = verificar_valores_estrictos(df, errores)
    advertencias = verificar_valores_advertencia(df, advertencias)

    _mostrar_resultado(errores, advertencias, total_filas)

    if errores:
        raise ValueError(f"Validacion fallida: {len(errores)} error(es) encontrado(s)")

    print("Validacion exitosa")



    if __name__ == "__main__":
        validate_csv()