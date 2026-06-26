"""
Carga de datos y ejecucion del pipeline.

Permite que un usuario cargue un CSV, lo deje en data/input del servidor y
dispare el DAG desde el navegador usando la API REST de Airflow.
"""

import os
import re
import json
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

# Columnas minimas que debe traer el CSV crudo.
# IMPORTANTE: ajustar esta lista al encabezado REAL de tu dataset.
# Si la dejas vacia (set()), se omite el chequeo de columnas.
EXPECTED_COLUMNS = {
    "purchase_date", "category", "subcategory", "brand", "device",
    "payment_method", "location", "price", "discount", "final_price",
    "rating", "review_count", "seller_id", "seller_rating",
    "shipping_time_days", "is_returned", "delivery_status",
}


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


def _norm_col(c):
    return re.sub(r"[\s_]+", "", str(c).strip().lower())


def _quick_validate(uploaded_file):
    """Validacion liviana al subir: lee solo el encabezado y una muestra del CSV
    (no el archivo completo) y chequea columnas, fechas y numericos.
    Devuelve (ok, problemas) con problemas = lista de mensajes."""
    problemas = []
    try:
        uploaded_file.seek(0)
        sample = pd.read_csv(uploaded_file, nrows=50)
    except Exception as exc:
        return False, [f"No se pudo leer el CSV: {exc}"]
    finally:
        try:
            uploaded_file.seek(0)
        except Exception:
            pass

    cols = list(sample.columns)
    cols_norm = {_norm_col(c) for c in cols}

    # 1) Columnas esperadas
    if EXPECTED_COLUMNS:
        faltantes = [c for c in EXPECTED_COLUMNS if _norm_col(c) not in cols_norm]
        if faltantes:
            problemas.append("Faltan columnas requeridas: " + ", ".join(sorted(faltantes)))

    # 2) Formato de fecha
    if any(_norm_col(c) == "purchasedate" for c in cols):
        col = next(c for c in cols if _norm_col(c) == "purchasedate")
        parsed = pd.to_datetime(sample[col], errors="coerce")
        if parsed.isna().all():
            problemas.append(f"La columna '{col}' no tiene un formato de fecha reconocible.")

    # 3) Numericos
    for esperado in ("price", "final_price", "discount", "rating"):
        match = next((c for c in cols if _norm_col(c) == _norm_col(esperado)), None)
        if match is not None:
            if pd.to_numeric(sample[match], errors="coerce").isna().all():
                problemas.append(f"La columna '{match}' no contiene valores numéricos.")

    return (len(problemas) == 0), problemas


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


def _format_detail(raw):
    """Convierte el detalle de errores/advertencias (texto, JSON o lista) en bullets."""
    if raw is None:
        return ""
    text = str(raw).strip()
    if not text or text.lower() in ("none", "null", "[]", "{}"):
        return ""
    items = None
    try:
        parsed = json.loads(text)
        if isinstance(parsed, list):
            items = [str(x) for x in parsed]
        elif isinstance(parsed, dict):
            items = [f"{k}: {v}" for k, v in parsed.items()]
    except Exception:
        pass
    if items is None:
        parts = re.split(r"[\n;]+", text)
        items = [p.strip() for p in parts if p.strip()]
    return "\n".join(f"- {it}" for it in items[:30])


def _latest_validation_detail(file_name):
    """Trae el detalle de errores/advertencias de la ultima validacion (defensivo)."""
    try:
        df = query("""
            SELECT errors, warnings
            FROM analytics.validation_summary
            WHERE file_name = %(fn)s
            ORDER BY validated_at DESC
            LIMIT 1
        """, {"fn": file_name})
        if df.empty:
            return "", ""
        return df["errors"].iloc[0] or "", df["warnings"].iloc[0] or ""
    except Exception:
        return "", ""


def _render_validation_alert():
    """Notificacion prominente del resultado de la ultima validacion (RF11)."""
    validations = _validation_rows(_processed_files())
    if validations is None or validations.empty:
        return

    latest = validations.iloc[0]
    status = str(latest.get("status", "")).strip().upper()
    fname = str(latest.get("file_name", ""))
    err_count = latest.get("error_count", 0)
    try:
        err_count = 0 if (err_count is None or pd.isna(err_count)) else int(err_count)
    except Exception:
        err_count = 0

    ok_status = status in ("SUCCESS", "PASSED", "OK", "VALID", "VALIDO", "VÁLIDO", "")
    failed = (not ok_status) or err_count > 0

    errors_detail, warnings_detail = _latest_validation_detail(fname)

    if failed:
        msg = (f"**Validación fallida** para `{fname}`. "
               f"El archivo no cumple la estructura esperada y no fue procesado.")
        detail = _format_detail(errors_detail)
        if detail:
            msg += "\n\n**Errores detectados:**\n" + detail
        elif err_count:
            msg += f"\n\nSe detectaron {err_count} error(es). Revisá la tabla de Validaciones."
        st.error(msg)
    else:
        st.success(f"Última validación correcta: `{fname}` cumple la estructura esperada.")
        wdetail = _format_detail(warnings_detail)
        if wdetail:
            st.warning("**Advertencias:**\n" + wdetail)


def _airflow_unavailable(exc):
    """Detecta si el error es porque Airflow todavia no esta accesible."""
    text = str(exc).lower()
    keys = ("connection refused", "max retries", "failed to establish",
            "newconnectionerror", "connectionerror", "timed out",
            "name or service not known", "connection aborted")
    if isinstance(exc, (requests.ConnectionError, requests.Timeout)):
        return True
    return any(k in text for k in keys)


_SPINNER_CSS = """
<style>
.ld-spin{display:inline-block;width:14px;height:14px;border:2px solid #cfdceb;
border-top-color:#2E6DA4;border-radius:50%;animation:ldspin .8s linear infinite;
vertical-align:middle;margin-right:6px;}
@keyframes ldspin{to{transform:rotate(360deg)}}
</style>
"""


def _state_style(state):
    s = (state or "").lower()
    if s in ("running", "queued", "scheduled", "up_for_retry"):
        return ("En ejecución", "#2E6DA4", "#EAF2FB", "running")
    if s == "success":
        return ("Completado", "#1A7F4B", "#E8F5EE", "success")
    if s in ("failed", "upstream_failed"):
        return ("Falló", "#C0392B", "#FBEAEA", "failed")
    return (state or "—", "#6B7A8D", "#F0F4F8", "other")


def _render_pipeline_status():
    """Muestra el estado de la ultima ejecucion con spinner mientras corre."""
    try:
        runs = list_dag_runs(limit=1)
    except Exception as exc:
        if _airflow_unavailable(exc):
            st.caption("El servicio de procesamiento todavía no está disponible. "
                       "Esperá unos segundos a que levante e intentá de nuevo.")
        return

    if not runs:
        return

    latest = runs[0]
    state = latest.get("state")
    label, color, bg, kind = _state_style(state)
    conf = latest.get("conf") or {}
    fname = conf.get("file_name", "")

    badge = (f'<span style="display:inline-block;padding:3px 12px;border-radius:14px;'
             f'background:{bg};color:{color};font-weight:600;font-size:0.82rem;">{label}</span>')

    if kind == "running":
        st.markdown(
            _SPINNER_CSS +
            f'<div style="padding:12px 16px;border:1px solid #D6E2F0;border-radius:8px;'
            f'background:#F7FAFD;margin-bottom:6px;">'
            f'<span class="ld-spin"></span>{badge} &nbsp; '
            f'Procesando <code>{fname}</code>… el pipeline corre en segundo plano y puede '
            f'tardar varios minutos. Podés seguir usando el dashboard mientras tanto.'
            f'</div>',
            unsafe_allow_html=True,
        )
        st.button("Actualizar estado", key="refresh_pipeline_status")
    elif kind == "success":
        run_id = latest.get("dag_run_id") or latest.get("run_id") or fname
        # Refresca el cache una sola vez por corrida, sin que el usuario haga nada.
        if st.session_state.get("refreshed_run_id") != run_id:
            st.session_state["refreshed_run_id"] = run_id
            st.cache_data.clear()
            st.rerun()
        st.markdown(
            f'<div style="padding:10px 16px;border:1px solid #CDE9D9;border-radius:8px;'
            f'background:#F1FbF5;margin-bottom:6px;">{badge} &nbsp; '
            f'<code>{fname}</code> procesado. El dashboard ya refleja los datos nuevos.'
            f'</div>', unsafe_allow_html=True,
        )
    elif kind == "failed":
        st.markdown(
            f'<div style="padding:10px 16px;border:1px solid #F0CFCF;border-radius:8px;'
            f'background:#FCF2F2;margin-bottom:6px;">{badge} &nbsp; '
            f'La ejecución de <code>{fname}</code> falló. Revisá la sección de Validaciones.'
            f'</div>', unsafe_allow_html=True,
        )


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
            ok, problemas = _quick_validate(uploaded)
            if not ok:
                st.error(
                    "**El archivo no cumple la estructura esperada:**\n"
                    + "\n".join(f"- {p}" for p in problemas)
                    + "\n\nCorregí el archivo y volvé a subirlo."
                )
            else:
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
                st.success(f"Pipeline iniciado para {last_file}")
        except requests.HTTPError as exc:
            detail = exc.response.text if exc.response is not None else str(exc)
            st.error(f"No se pudo ejecutar el pipeline: {detail}")
        except Exception as exc:
            if _airflow_unavailable(exc):
                st.error("No se pudo iniciar el pipeline: el servicio de Airflow no está "
                         "disponible. Verificá que los contenedores estén iniciados.")
            else:
                st.error(f"No se pudo ejecutar el pipeline: {exc}")

if last_file:
    st.info(f"Ultimo archivo cargado en esta sesion: {last_file}")

# ── Estado de la ultima ejecucion (spinner mientras corre) ──
_render_pipeline_status()

# ── Resultado de la ultima validacion — RF11 ──
_render_validation_alert()

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
        if _airflow_unavailable(exc):
            st.caption("El servicio de Airflow no está disponible por el momento. "
                       "Verificá que los contenedores estén iniciados o esperá unos segundos.")
        else:
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