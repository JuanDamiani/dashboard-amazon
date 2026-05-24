# Amazon E-Commerce Dashboard

Proyecto de ingenieria de datos con Airflow, PostgreSQL y Metabase para procesar un CSV de e-commerce y exponer datos analiticos.

## Requisitos

- Docker Desktop
- Docker Compose v2
- Git

## Primera Instalacion

Clonar el repositorio y entrar a la carpeta del proyecto.

```powershell
docker compose up -d --build
```

El proyecto tiene defaults en `docker-compose.yml`, por lo que puede levantarse sin crear un `.env`.

Si queres personalizar puertos o credenciales, copia `.env.example` a `.env` y cambia los valores necesarios. El archivo `.env` es local y no se versiona.

## Uso Posterior

Para levantar servicios ya construidos:

```powershell
docker compose up -d
```

Para ver el estado:

```powershell
docker compose ps
```

## URLs

- Airflow: http://localhost:8080
- Metabase: http://localhost:3000

Si cambias `AIRFLOW_PORT` o `METABASE_PORT`, usa esos puertos en lugar de `8080` y `3000`.

## Credenciales

Airflow crea el usuario inicial:

- Usuario: `admin`
- Password: `admin`

Metabase usa su asistente de configuracion inicial en el primer ingreso.

## Ejecutar El Pipeline

El DAG `amazon_pipeline` corre cada 5 minutos. Busca archivos `*.csv` en `data/input`, selecciona el CSV mas antiguo que todavia no figure en `analytics.processed_files` con el mismo hash de contenido, y procesa un archivo por corrida. Si no hay CSV pendientes, la corrida se saltea.

Para ejecutarlo manualmente:

1. Entrar a Airflow.
2. Buscar el DAG `amazon_pipeline`.
3. Activarlo si esta pausado.
4. Presionar Trigger DAG.

El flujo esperado es:

```text
check_input_file_available -> check_file_not_processed -> audit_pipeline_start
-> validate_csv -> load_staging -> clean_staging
-> KPIs en paralelo -> run_quality_checks -> register_processed_file
-> audit_pipeline_success -> notify_success
```

Cada mart/KPI tiene una tarea propia en Airflow para facilitar trazabilidad y ejecucion paralela.

Para archivos grandes, el ETL evita cargar todo el dataset completo en memoria:

- `validate_csv` valida por chunks.
- `load_staging` carga por chunks en `staging.amazon_sales_input`, una staging tabular, usando `COPY` de PostgreSQL.
- `clean_staging` deduplica y transforma hacia `analytics.fact_orders` con SQL y `ON CONFLICT DO NOTHING`.
- `load_staging` y `clean_staging` ejecutan `ANALYZE` para actualizar estadisticas despues de cargas grandes.
- Los marts se recalculan con SQL desde `analytics.fact_orders`.

Para incorporar un nuevo dataset, copiar el archivo CSV a `data/input`. No hace falta que se llame `amazon_ecommerce.csv`; por ejemplo, `amazon_ecommerce_1M.csv` sera detectado si todavia no fue procesado.

Cuando una corrida termina correctamente, el CSV se registra en `analytics.processed_files` y se mueve a `data/processed`. Si falla, se registra el fallo en `analytics.etl_audit_log`, se guarda el resumen en `analytics.validation_summary` cuando aplica, y el archivo se mueve a `data/rejected` para evitar reintentos infinitos.

## Conectar Metabase Al Data Warehouse

En el asistente de Metabase, agregar una base PostgreSQL con estos valores por defecto:

- Host: `postgres-dwh`
- Puerto: `5432`
- Base: `amazon_dwh`
- Usuario: `dwh`
- Password: `dwh123`

Si cambias las variables `DWH_DB_*`, usa esos nuevos valores al configurar Metabase.

## Dashboard Y SRS

La cobertura del SRS y el glosario de indicadores estan documentados en:

- `docs/cobertura_srs_dashboard.md`
- `docs/glosario_kpis.md`

Metabase se configura desde la interfaz. Para dejar evidencia de entrega, se recomienda crear los dashboards indicados en `docs/cobertura_srs_dashboard.md` y anexar capturas.

## Variables De Entorno

Las variables principales estan documentadas en `.env.example`.

Puertos:

- `AIRFLOW_PORT`
- `METABASE_PORT`

Base de metadata de Airflow:

- `AIRFLOW_DB_USER`
- `AIRFLOW_DB_PASSWORD`
- `AIRFLOW_DB_NAME`

Data Warehouse:

- `DWH_DB_USER`
- `DWH_DB_PASSWORD`
- `DWH_DB_HOST`
- `DWH_DB_PORT`
- `DWH_DB_NAME`
- `AIRFLOW_CONN_POSTGRES_DWH`
- `DB_URL`

Base interna de Metabase:

- `METABASE_DB_USER`
- `METABASE_DB_PASSWORD`
- `METABASE_DB_NAME`

Los scripts Python construyen `DB_URL` desde `DWH_DB_*` si no se define manualmente.

## Logs

Logs de todos los servicios:

```powershell
docker compose logs
```

Logs de un servicio:

```powershell
docker compose logs airflow-webserver
docker compose logs airflow-scheduler
docker compose logs postgres-dwh
docker compose logs metabase
```

Seguir logs en vivo:

```powershell
docker compose logs -f
```

## Tests

Las pruebas estan pensadas para ejecutarse dentro del contenedor de Airflow, sin instalar Python en la maquina host:

```powershell
docker compose run --rm airflow-scheduler python -m unittest discover -s /opt/airflow/tests -t /opt/airflow
```

Si usas Git Bash en Windows, evita que convierta las rutas Linux del contenedor:

```bash
MSYS_NO_PATHCONV=1 docker compose run --rm airflow-scheduler python -m unittest discover -s /opt/airflow/tests -t /opt/airflow
```

Tambien se puede validar compilacion de modulos:

```powershell
docker compose run --rm airflow-scheduler python -m compileall /opt/airflow/dags /opt/airflow/scripts /opt/airflow/tests
```

En Git Bash:

```bash
MSYS_NO_PATHCONV=1 docker compose run --rm airflow-scheduler python -m compileall /opt/airflow/dags /opt/airflow/scripts /opt/airflow/tests
```

## Apagado

Detener servicios sin borrar volumenes:

```powershell
docker compose down
```

## Reinicio Limpio

Esto borra los volumenes de PostgreSQL y Metabase. Usalo solo cuando quieras empezar desde cero.

```powershell
docker compose down -v
docker compose up -d --build
```

## Problemas Comunes

Si Airflow o Metabase no levantan porque el puerto esta ocupado, cambia `AIRFLOW_PORT` o `METABASE_PORT` en `.env`.

Si aparece un warning similar a `Error loading config file: C:\Users\...\ .docker\config.json: Acceso denegado`, corresponde a permisos locales de Docker Desktop en Windows. No es un error del proyecto.

Si cambias credenciales o nombres de base con volumenes ya creados, PostgreSQL puede conservar la configuracion anterior. Para aplicar cambios de base desde cero, usa el reinicio limpio.
