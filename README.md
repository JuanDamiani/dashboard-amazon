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

1. Entrar a Airflow.
2. Buscar el DAG `amazon_pipeline`.
3. Activarlo si esta pausado.
4. Presionar Trigger DAG.

El flujo esperado es:

```text
validate_csv -> load_staging -> clean_staging -> build_kpis
```

## Conectar Metabase Al Data Warehouse

En el asistente de Metabase, agregar una base PostgreSQL con estos valores por defecto:

- Host: `postgres-dwh`
- Puerto: `5432`
- Base: `amazon_dwh`
- Usuario: `dwh`
- Password: `dwh123`

Si cambias las variables `DWH_DB_*`, usa esos nuevos valores al configurar Metabase.

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
