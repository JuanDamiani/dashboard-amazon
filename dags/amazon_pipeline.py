from datetime import datetime

from airflow import DAG
from airflow.operators.python import PythonOperator

from scripts.validation.validate_csv import validate_csv
from scripts.load.load_staging import load_staging
from scripts.transform.clean_staging import clean_staging
from scripts.build_kpis import build_kpis


default_args = {
    "owner": "amazon-team",
    "retries": 1
}


with DAG(
    dag_id="amazon_pipeline",
    default_args=default_args,
    start_date=datetime(2026, 1, 1),
    schedule_interval=None,
    catchup=False,
    tags=["amazon", "etl"]
) as dag:

    validate_task = PythonOperator(
        task_id="validate_csv",
        python_callable=validate_csv
    )

    load_task = PythonOperator(
        task_id="load_staging",
        python_callable=load_staging
    )

    clean_task = PythonOperator(
        task_id="clean_staging",
        python_callable=clean_staging
    )

    kpi_task = PythonOperator(
        task_id="build_kpis",
        python_callable=build_kpis
    )

    validate_task >> load_task >> clean_task >> kpi_task
