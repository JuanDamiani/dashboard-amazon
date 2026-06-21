# Cobertura SRS - Dashboard Streamlit

Este documento deja evidencia de que visualizacion, tabla o flujo cubre cada
requisito funcional del dashboard.

| Requisito | Cobertura en Streamlit / Airflow | Fuente |
| --- | --- | --- |
| RF1 Resumen ejecutivo | KPIs principales, ingresos por categoria, estado de entregas, metodos de pago y dispositivos. | `dashboard/pages/01_overview.py`, `analytics.fact_orders` |
| RF2 Filtros globales | Filtros persistentes de periodo, categoria, ciudad, dispositivo y metodo de pago; filtros locales por seccion. | `dashboard/utils/filters.py` |
| RF3 Analisis de ventas | Evolucion mensual, ventas por categoria, subcategoria, marca, precios y descuentos. | `dashboard/pages/02_ventas.py` |
| RF4 Analisis logistico | Estado de entrega, tiempo por ciudad, devoluciones, demoras y relacion pago/devolucion. | `dashboard/pages/03_logistica.py` |
| RF5 Experiencia del cliente | Distribucion de ratings, rating por categoria/ciudad, efecto de envio y dispositivo. | `dashboard/pages/04_clientes.py` |
| RF6 Analisis de vendedores | Ranking, rating, devoluciones, ingresos y categorias por vendedor. | `dashboard/pages/05_vendedores.py` |
| RF7 Exportacion CSV | Botones de descarga CSV en paginas del dashboard y tablas operativas. | `dashboard/utils/downloads.py`, paginas Streamlit |
| RF8 Navegacion entre paginas | Navegacion horizontal: Carga, Overview, Ventas, Logistica, Clientes, Vendedores y Glosario. | `dashboard/app.py` |
| RF9 Tutorial y glosario | Definiciones, formulas e interpretacion de KPIs. | `dashboard/pages/06_glosario.py`, `docs/glosario_kpis.md` |
| RF10 Ingesta de archivos | Upload desde navegador y ejecucion bajo demanda del archivo cargado. | `dashboard/pages/00_carga.py`, `dags/amazon_pipeline.py` |
| RF11 Validacion de estructura | Validacion de columnas, tipos, fechas, rangos y valores permitidos. | `scripts/validation/validate_csv.py` |
| RF12 Procesamiento automatizado | Flujo Airflow: validacion, staging, limpieza, fact table y marts. | `dags/amazon_pipeline.py` |
| RF13 Notificacion de estado | Auditoria, logs y consulta de estado desde Streamlit. | `scripts/utils/notify_status.py`, `scripts/utils/audit.py`, `dashboard/pages/00_carga.py` |
| RF14 Persistencia historica | Carga append en fact table, control de archivos procesados y movimiento a `processed` o `rejected`. | `scripts/load/load_staging.py`, `scripts/transform/clean_staging.py`, `scripts/utils/register_processed_file.py`, `scripts/utils/file_lifecycle.py` |

## Flujo De Usuario

1. El usuario entra a Streamlit.
2. Sube un CSV en la pestaña `Carga`.
3. Streamlit guarda el archivo en `data/input` del servidor.
4. Streamlit dispara `amazon_pipeline` por API REST de Airflow.
5. Airflow procesa el archivo indicado en `dag_run.conf`.
6. El usuario consulta estado, dashboard y descargas desde el navegador.

## Evidencia Recomendada Para La Entrega

1. Captura de upload de CSV.
2. Captura de ejecucion iniciada.
3. Captura de estado exitoso.
4. Captura de dashboard actualizado.
5. Captura de descarga CSV.
6. Captura de validacion fallida con CSV invalido.
