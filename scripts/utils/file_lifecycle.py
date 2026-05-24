"""
Movimiento de archivos segun resultado del pipeline.

Este modulo implementa RF10, RF13 y RF14. Cuando un CSV termina correctamente,
se mueve a data/processed para no volver a tomarlo desde input. Si falla, se
mueve a data/rejected para evitar reintentos infinitos sin diagnostico.
"""

import shutil
from datetime import datetime
from pathlib import Path

from scripts.config import PROCESSED_DIR, REJECTED_DIR
from scripts.utils.input_file import get_selected_csv_path


def _unique_target(directory, file_name):
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / file_name
    if not target.exists():
        return target

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = Path(file_name)
    return directory / f"{path.stem}_{timestamp}{path.suffix}"


def move_selected_file(context, target_dir, status_label):
    file_path = get_selected_csv_path(context)
    if not file_path.exists():
        print(f"Archivo no encontrado para mover a {status_label}: {file_path}")
        return None

    target = _unique_target(target_dir, file_path.name)
    shutil.move(str(file_path), str(target))
    print(f"Archivo movido a {status_label}: {target}")
    return str(target)


def move_processed_file(**context):
    return move_selected_file(context, PROCESSED_DIR, "processed")


def move_rejected_file(context):
    return move_selected_file(context, REJECTED_DIR, "rejected")

