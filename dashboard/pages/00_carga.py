"""
Carga de datos y ejecucion del pipeline.

Permite que un usuario cargue un CSV, lo deje en data/input del servidor y
dispare el DAG desde el navegador usando la API REST de Airflow.
"""

import os
import re
import uuid
from datetime import datetime
from pathlib import Path

import pandas as pd
import requests
import streamlit as st

from utils.airflow_api import active_dag_runs, list_dag_runs, trigger_pipeline, unpause_dag
from utils.db import query
from utils.downloads import download_dataframe
from utils.style import PALETTE


INPUT_DIR = Path(os.getenv("DASHBOARD_INPUT_DIR", "/data/input"))
TMP_DIR = Path(os.getenv("DASHBOARD_UPLOAD_TMP_DIR", "/data/uploads_tmp"))
MAX_UPLOAD_MB = int(os.getenv("DASHBOARD_MAX_UPLOAD_MB", "500"))


def _safe_name(name):
    stem = Path(name).stem
    stem = re.sub(r"[^A-Za-z0-9_.-]+", "_", stem).strip("._")
    return stem or "dataset"


def _target_name(original_name):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    suffix = uuid.uuid4().hex[:8]
    return f"{timestamp}_{suffix}_{_safe_name(original_name)}.csv"


def _save_upload(uploaded_file):
    if not uploaded_file.name.lower().endswith(".csv"):
        raise ValueError("El archivo debe tener extension .csv")

    size_mb = uploaded_file.size / (1024 * 1024)
    if size_mb > MAX_UPLOAD_MB:
        raise ValueError(f"El archivo supera el limite de {MAX_UPLOAD_MB} MB")

    INPUT_DIR.mkdir(parents=True, exist_ok=True)
    TMP_DIR.mkdir(parents=True, exist_ok=True)

    file_name = _target_name(uploaded_file.name)
    tmp_path = TMP_DIR / f"{file_name}.uploading"
    final_path = INPUT_DIR / file_name

    with tmp_path.open("wb") as file:
        file.write(uploaded_file.getbuffer())
    tmp_path.replace(final_path)
    return file_name, final_path


def _runs_dataframe(runs):
    rows = []
    for run in runs:
        conf = run.get("conf") or {}
        rows.append({
            "dag_run_id": run.get("dag_run_id"),
            "archivo": conf.get("file_name", ""),
            "estado": run.get("state"),
            "inicio": run.get("start_date") or run.get("execution_date"),
            "fin": run.get("end_date"),
        })
    return pd.DataFrame(rows)


def _processed_files():
    try:
        return query("""
            SELECT file_name, batch_id, processed_at
            FROM analytics.processed_files
            ORDER BY processed_at DESC
            LIMIT 50
        """)
    except Exception:
        return pd.DataFrame(columns=["file_name", "batch_id", "processed_at"])


def _validation_rows(processed):
    try:
        validations = query("""
            SELECT file_name, status, rows_total, error_count, warning_count, validated_at
            FROM analytics.validation_summary
            ORDER BY validated_at DESC
            LIMIT 50
        """)
    except Exception:
        validations = pd.DataFrame()

    if not validations.empty:
        return validations

    if processed.empty:
        return validations

    fallback = processed.copy()
    fallback["status"] = "SUCCESS"
    fallback["rows_total"] = None
    fallback["error_count"] = 0
    fallback["warning_count"] = None
    fallback = fallback.rename(columns={"processed_at": "validated_at"})
    return fallback[["file_name", "status", "rows_total", "error_count", "warning_count", "validated_at"]]


st.markdown(f"""
<div style="margin-bottom: 18px;">
  <div style="font-size:1.3rem;font-weight:700;color:{PALETTE['primary']};">Carga de datos</div>
  <div style="font-size:0.88rem;color:{PALETTE['text_light']};">
    Subi un CSV, ejecuta el pipeline y consulta el resultado desde el navegador.
  </div>
</div>
""", unsafe_allow_html=True)

st.caption("Archivo CSV")
uploaded = st.file_uploader(
    "Seleccionar CSV",
    type=["csv"],
    accept_multiple_files=False,
    label_visibility="collapsed",
)

col_upload, col_run = st.columns([1, 1])
with col_upload:
    if st.button("Guardar archivo", use_container_width=True, disabled=uploaded is None):
        try:
            saved_name, saved_path = _save_upload(uploaded)
            st.session_state["last_uploaded_file"] = saved_name
            st.success(f"Archivo recibido: {saved_name}")
            st.caption(f"Guardado en servidor: {saved_path}")
        except Exception as exc:
            st.error(str(exc))

last_file = st.session_state.get("last_uploaded_file")
with col_run:
    if st.button("Ejecutar pipeline", use_container_width=True, disabled=not last_file):
        try:
            running = active_dag_runs()
            if running:
                st.warning("El pipeline ya esta en ejecucion o en cola. Espera a que termine antes de lanzar otro.")
            else:
                unpause_dag()
                run = trigger_pipeline(last_file)
                st.session_state["last_dag_run_id"] = run.get("dag_run_id")
                st.cache_data.clear()
                st.success(f"Pipeline iniciado para {last_file}")
        except requests.HTTPError as exc:
            detail = exc.response.text if exc.response is not None else str(exc)
            st.error(f"No se pudo ejecutar el pipeline: {detail}")
        except Exception as exc:
            st.error(f"No se pudo ejecutar el pipeline: {exc}")

if last_file:
    st.info(f"Ultimo archivo cargado en esta sesion: {last_file}")

st.markdown("<br>", unsafe_allow_html=True)

col_state, col_processed, col_validation = st.columns([1.2, 1, 1])

with col_state:
    st.markdown("**Ultimas ejecuciones**")
    try:
        runs_df = _runs_dataframe(list_dag_runs(limit=8))
        if runs_df.empty:
            st.caption("Todavia no hay ejecuciones registradas.")
        else:
            st.dataframe(runs_df, use_container_width=True, height=260)
            download_dataframe(runs_df, "ejecuciones_pipeline.csv", "Descargar ejecuciones", "runs_csv")
    except Exception as exc:
        st.warning(f"No se pudo consultar Airflow: {exc}")

with col_processed:
    st.markdown("**Archivos procesados**")
    try:
        processed = _processed_files()
        if processed.empty:
            st.caption("Sin archivos procesados.")
        else:
            processed_view = processed.head(10)
            st.dataframe(processed_view, use_container_width=True, height=260)
            download_dataframe(processed_view, "archivos_procesados.csv", "Descargar procesados", "processed_csv")
    except Exception as exc:
        st.warning(f"No se pudo consultar archivos procesados: {exc}")

with col_validation:
    st.markdown("**Validaciones**")
    try:
        processed_for_validation = _processed_files()
        validations = _validation_rows(processed_for_validation)
        if validations.empty:
            st.caption("Sin validaciones registradas.")
        else:
            validations_view = validations.head(10)
            st.dataframe(validations_view, use_container_width=True, height=260)
            download_dataframe(validations_view, "validaciones.csv", "Descargar validaciones", "validations_csv")
    except Exception as exc:
        st.warning(f"No se pudo consultar validaciones: {exc}")

st.markdown("<br>", unsafe_allow_html=True)
st.markdown("**Archivos pendientes en servidor**")
try:
    INPUT_DIR.mkdir(parents=True, exist_ok=True)
    processed_names = set(_processed_files()["file_name"].tolist())
    pending_rows = []
    for path in sorted(INPUT_DIR.glob("*.csv"), key=lambda item: item.stat().st_mtime):
        if path.name in processed_names:
            continue
        stat = path.stat()
        pending_rows.append({
            "archivo": path.name,
            "tamano_mb": round(stat.st_size / (1024 * 1024), 2),
            "modificado": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
        })
    pending = pd.DataFrame(pending_rows)
    if pending.empty:
        st.caption("No hay CSVs pendientes en data/input.")
    else:
        st.dataframe(pending, use_container_width=True, height=220)
        download_dataframe(pending, "archivos_pendientes.csv", "Descargar pendientes", "pending_csv")
except Exception as exc:
    st.warning(f"No se pudo listar la carpeta de entrada: {exc}")
