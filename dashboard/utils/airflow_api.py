"""Small Airflow REST API client used by the Streamlit dashboard."""

import os
from datetime import datetime, timezone

import requests


DAG_ID = os.getenv("AIRFLOW_DAG_ID", "amazon_pipeline")
API_URL = os.getenv("AIRFLOW_API_URL", "http://airflow-webserver:8080/api/v1").rstrip("/")
API_USER = os.getenv("AIRFLOW_API_USER", "admin")
API_PASSWORD = os.getenv("AIRFLOW_API_PASSWORD", "admin")
TIMEOUT = int(os.getenv("AIRFLOW_API_TIMEOUT", "15"))


def _request(method, path, **kwargs):
    url = f"{API_URL}{path}"
    response = requests.request(
        method,
        url,
        auth=(API_USER, API_PASSWORD),
        timeout=TIMEOUT,
        **kwargs,
    )
    response.raise_for_status()
    if response.content:
        return response.json()
    return {}


def unpause_dag():
    return _request("PATCH", f"/dags/{DAG_ID}", json={"is_paused": False})


def list_dag_runs(limit=10):
    data = _request(
        "GET",
        f"/dags/{DAG_ID}/dagRuns",
        params={"order_by": "-execution_date", "limit": limit},
    )
    return data.get("dag_runs", [])


def active_dag_runs():
    return [run for run in list_dag_runs(limit=20) if run.get("state") in {"queued", "running"}]


def trigger_pipeline(file_name):
    run_id = datetime.now(timezone.utc).strftime("manual__upload__%Y%m%dT%H%M%S%fZ")
    payload = {
        "dag_run_id": run_id,
        "conf": {"file_name": file_name},
    }
    return _request("POST", f"/dags/{DAG_ID}/dagRuns", json=payload)
