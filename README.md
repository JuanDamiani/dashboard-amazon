# Amazon E-Commerce Dashboard

Proyecto de ingenieria de datos con Airflow, PostgreSQL y Streamlit. Procesa
archivos CSV de e-commerce, carga un data warehouse y expone un dashboard web
para cargar datos, ejecutar el pipeline, consultar estado, visualizar KPIs y
descargar resultados.

## Requisitos

- Docker Desktop
- Docker Compose v2
- Git

## Primera Instalacion

```powershell
docker compose up -d --build
```

El stack queda disponible en:

- Streamlit: http://localhost:8501
- Airflow: http://localhost:8080

Credenciales Airflow por defecto:

- Usuario: `admin`
- Password: `admin`

Credenciales Streamlit por defecto:

- Usuario: `admin`
- Password: `admin`

## Uso Para Usuario Final

El usuario final puede trabajar desde Streamlit sin acceder a carpetas ni a
Docker:

1. Entrar a http://localhost:8501.
2. Iniciar sesion con las credenciales del dashboard.
3. Abrir la pestaña `Carga`.
4. Subir un archivo `.csv`.
5. Presionar `Guardar archivo`.
6. Presionar `Ejecutar pipeline`.
7. Consultar el estado de ejecucion en la misma pantalla.
8. Navegar a las paginas del dashboard cuando el pipeline finalice.
9. Descargar CSVs desde las tablas o vistas disponibles.

Streamlit guarda el archivo en el servidor dentro de `data/input`. Esa carpeta
esta montada en los contenedores de Airflow como `/opt/airflow/data/input`.

## Flujo Automatizado

El DAG `amazon_pipeline` se ejecuta bajo demanda desde Streamlit o desde la UI
de Airflow. Cuando Streamlit dispara el DAG por API REST, envia el nombre exacto
del archivo cargado y Airflow procesa ese archivo especifico. Si se ejecuta
manualmente sin parametro, toma el CSV mas antiguo pendiente en `data/input`.

Flujo principal:

```text
check_input_file_available -> check_file_not_processed -> audit_pipeline_start
-> validate_csv -> load_staging -> clean_staging
-> KPIs en tandas -> run_quality_checks -> register_processed_file
-> audit_pipeline_success -> move_processed_file -> notify_success
```

Si el procesamiento termina correctamente, el CSV se mueve a `data/processed`.
Si falla, se registra el error y el archivo se mueve a `data/rejected`.

## Formato Del CSV

Columnas requeridas:

```text
user_id, product_id, category, subcategory, brand, price, discount,
final_price, rating, review_count, stock, seller_id, seller_rating,
purchase_date, shipping_time_days, location, device, payment_method,
is_returned, delivery_status
```

El pipeline detecta separador `,` o `;` automaticamente.

## Arquitectura

- `postgres-airflow`: metadata de Airflow.
- `postgres-dwh`: data warehouse analitico.
- `airflow-init`: inicializa DB y usuario admin.
- `airflow-scheduler`: agenda y ejecuta tareas.
- `airflow-webserver`: UI y API REST de Airflow.
- `streamlit`: interfaz de usuario y dashboard.

## Variables Principales

Puertos:

- `AIRFLOW_PORT`

Data warehouse:

- `DWH_DB_USER`
- `DWH_DB_PASSWORD`
- `DWH_DB_HOST`
- `DWH_DB_PORT`
- `DWH_DB_NAME`
- `AIRFLOW_CONN_POSTGRES_DWH`
- `DB_URL`

API de Airflow usada por Streamlit:

- `AIRFLOW_API_USER`
- `AIRFLOW_API_PASSWORD`

Acceso al dashboard:

- `DASHBOARD_AUTH_USER`
- `DASHBOARD_AUTH_PASSWORD`

## Dashboard

Paginas:

- `Carga`: upload de CSV, ejecucion del pipeline, estado y descargas operativas.
- `Overview`: resumen ejecutivo.
- `Ventas`: analisis comercial.
- `Logistica`: entregas, demoras y devoluciones.
- `Clientes`: rating y experiencia.
- `Vendedores`: performance por seller.
- `Glosario`: definiciones de KPIs.

## Logs

```powershell
docker compose logs
docker compose logs airflow-webserver
docker compose logs airflow-scheduler
docker compose logs streamlit
docker compose logs postgres-dwh
```

## Tests

Las pruebas estan pensadas para ejecutarse dentro del contenedor de Airflow:

```powershell
docker compose run --rm airflow-scheduler python -m unittest discover -s /opt/airflow/tests -t /opt/airflow
```

Validacion de compilacion:

```powershell
docker compose run --rm airflow-scheduler python -m compileall /opt/airflow/dags /opt/airflow/scripts /opt/airflow/tests
```

## Apagado

```powershell
docker compose down
```

## Reinicio Limpio

Esto borra los volumenes de PostgreSQL y reinicia las bases desde cero.

```powershell
docker compose down -v
docker compose up -d --build
```
