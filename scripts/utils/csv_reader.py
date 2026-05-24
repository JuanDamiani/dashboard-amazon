"""
Lectura comun de archivos CSV.

Este modulo apoya RF10 y RF11. Permite que el pipeline procese archivos CSV con
separador punto y coma o coma, manteniendo una unica logica de lectura para
validacion y carga Bronze.
"""

import csv

import pandas as pd

from scripts.config import CSV_SEPARATOR


def detect_csv_separator(file_path):
    """Detects the most likely delimiter for the selected CSV."""
    with open(file_path, "r", encoding="utf-8-sig", newline="") as file:
        sample = file.read(8192)

    if not sample:
        return CSV_SEPARATOR

    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=";,")
        return dialect.delimiter
    except csv.Error:
        header = sample.splitlines()[0] if sample.splitlines() else ""
        comma_count = header.count(",")
        semicolon_count = header.count(";")
        return "," if comma_count > semicolon_count else CSV_SEPARATOR


def read_csv_auto(file_path, dtype=None, nrows=None, chunksize=None):
    """Reads a CSV using the detected delimiter."""
    separator = detect_csv_separator(file_path)
    df = pd.read_csv(file_path, sep=separator, dtype=dtype, nrows=nrows, chunksize=chunksize)
    print(f"Separador detectado para {file_path.name}: {separator}")
    return df
