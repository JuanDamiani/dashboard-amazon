"""
DAG principal del sistema Amazon E-Commerce.

Segun el SRS, este archivo cubre los requisitos de Gestion de Datos y
Automatizacion: RF10 ingesta de archivos, RF11 validacion de estructura,
RF12 procesamiento ETL, RF13 notificacion de estado y RF14 persistencia
historica. Tambien apoya RNF-10 porque separa el flujo en tareas pequenas:
validacion, carga, limpieza, KPIs, auditoria y notificacion.
"""

from datetime import datetime

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.utils.trigger_rule import TriggerRule

# KPIs originales
from scripts.kpis.customer_experience import build_customer_experience
from scripts.kpis.device_sales import build_device_sales
from scripts.kpis.logistics import build_logistics
from scripts.kpis.logistics_by_city import build_logistics_by_city
from scripts.kpis.monthly_delays import build_monthly_delays
from scripts.kpis.monthly_sales import build_monthly_sales
from scripts.kpis.payment_methods import build_payment_methods
from scripts.kpis.period_variation import build_period_variation
from scripts.kpis.returns import build_returns
from scripts.kpis.sales_by_brand import build_sales_by_brand
from scripts.kpis.sales_by_category import build_sales_by_category
from scripts.kpis.sales_summary import build_sales_summary
from scripts.kpis.satisfaction_by_city import build_satisfaction_by_city
from scripts.kpis.seller_performance import build_seller_performance

# KPIs nuevos — cubren los faltantes del SRS
from scripts.kpis.delivery_performance import build_delivery_performance
from scripts.kpis.payment_vs_returns import build_payment_vs_returns
from scripts.kpis.delays_vs_returns import build_delays_vs_returns
from scripts.kpis.rating_distribution import build_rating_distribution
from scripts.kpis.categories_by_seller import build_categories_by_seller
from scripts.kpis.discount_vs_orders import build_discount_vs_orders

from scripts.load.load_staging import load_staging
from scripts.transform.clean_staging import clean_staging
from scripts.utils.audit import log_pipeline_start, log_pipeline_success
from scripts.utils.file_lifecycle import move_processed_file
from scripts.utils.input_file import check_input_file_available
from scripts.utils.notify_status import notify_failure, notify_success
from scripts.utils.quality_checks import run_quality_checks
from scripts.utils.register_processed_file import check_file_not_processed, register_processed_file
from scripts.validation.validate_csv import validate_csv


default_args = {
    "owner": "amazon-team",
    "retries": 0,
}


KPI_TASKS = {
    # ── KPIs originales ──────────────────────────────────
    "build_sales_summary":       build_sales_summary,       # RF1
    "build_sales_by_category":   build_sales_by_category,   # RF1, RF3
    "build_sales_by_brand":      build_sales_by_brand,      # RF3
    "build_logistics":           build_logistics,            # RF1, RF4
    "build_payment_methods":     build_payment_methods,     # RF1
    "build_returns":             build_returns,              # RF4, RF5
    "build_monthly_sales":       build_monthly_sales,       # RF3
    "build_device_sales":        build_device_sales,        # RF1, RF3, RF5
    "build_customer_experience": build_customer_experience, # RF5
    "build_satisfaction_by_city":build_satisfaction_by_city,# RF5
    "build_seller_performance":  build_seller_performance,  # RF6
    "build_logistics_by_city":   build_logistics_by_city,   # RF4
    "build_monthly_delays":      build_monthly_delays,      # RF4
    "build_period_variation":    build_period_variation,    # RF1, RF3

    # ── KPIs nuevos ──────────────────────────────────────
    "build_delivery_performance": build_delivery_performance, # RF4: % entregas a tiempo, % demorados
    "build_payment_vs_returns":   build_payment_vs_returns,   # RF4: metodo de pago vs devolucion
    "build_delays_vs_returns":    build_delays_vs_returns,    # RF4: demoras vs devoluciones
    "build_rating_distribution":  build_rating_distribution,  # RF5: distribucion ratings y rating por rango
    "build_categories_by_seller": build_categories_by_seller, # RF6: categorias por vendedor
    "build_discount_vs_orders":   build_discount_vs_orders,   # RF3: descuento vs volumen ordenes
}

# En instalaciones locales con LocalExecutor, disparar todos los KPIs a la vez
# puede saturar el heartbeat de Airflow contra su base de metadata. Se mantienen
# tareas separadas y paralelismo, pero en tandas chicas para que el DAG sea
# estable incluso con CSVs grandes y contenedores recien levantados.
# Con 20 KPIs: sqrt(20) ≈ 4.5 → redondeado a 4 para mayor estabilidad.
KPI_PARALLEL_BATCH_SIZE = 4


def chunk_tasks(tasks, chunk_size):
    """Divide una lista de tareas en tandas de ejecucion paralela."""
    return [tasks[index:index + chunk_size] for index in range(0, len(tasks), chunk_size)]


with DAG(
    dag_id="amazon_pipeline",
    default_args=default_args,
    start_date=datetime(2026, 1, 1),
    schedule_interval="*/5 * * * *",
    catchup=False,
    max_active_runs=1,
    tags=["amazon", "etl"],
    on_failure_callback=notify_failure,
) as dag:

    check_file_available_task = PythonOperator(
        task_id="check_input_file_available",
        python_callable=check_input_file_available,
    )

    check_not_processed_task = PythonOperator(
        task_id="check_file_not_processed",
        python_callable=check_file_not_processed,
    )

    audit_start_task = PythonOperator(
        task_id="audit_pipeline_start",
        python_callable=log_pipeline_start,
    )

    validate_task = PythonOperator(
        task_id="validate_csv",
        python_callable=validate_csv,
    )

    load_task = PythonOperator(
        task_id="load_staging",
        python_callable=load_staging,
    )

    clean_task = PythonOperator(
        task_id="clean_staging",
        python_callable=clean_staging,
    )

    kpi_tasks = [
        PythonOperator(
            task_id=task_id,
            python_callable=callable_,
        )
        for task_id, callable_ in KPI_TASKS.items()
    ]
    kpi_batches = chunk_tasks(kpi_tasks, KPI_PARALLEL_BATCH_SIZE)

    quality_task = PythonOperator(
        task_id="run_quality_checks",
        python_callable=run_quality_checks,
        trigger_rule=TriggerRule.ALL_SUCCESS,
    )

    register_file_task = PythonOperator(
        task_id="register_processed_file",
        python_callable=register_processed_file,
    )

    audit_success_task = PythonOperator(
        task_id="audit_pipeline_success",
        python_callable=log_pipeline_success,
    )

    notify_success_task = PythonOperator(
        task_id="notify_success",
        python_callable=notify_success,
    )

    move_processed_task = PythonOperator(
        task_id="move_processed_file",
        python_callable=move_processed_file,
    )

    (
        check_file_available_task
        >> check_not_processed_task
        >> audit_start_task
        >> validate_task
        >> load_task
        >> clean_task
        >> kpi_batches[0]
    )

    for current_batch, next_batch in zip(kpi_batches, kpi_batches[1:]):
        for upstream_task in current_batch:
            upstream_task >> next_batch

    (
        kpi_batches[-1]
        >> quality_task
        >> register_file_task
        >> audit_success_task
        >> move_processed_task
        >> notify_success_task
    )