# Cobertura SRS - Dashboard

Este documento deja evidencia de que visualizacion o tabla cubre cada requisito funcional del dashboard.

| Requisito | Cobertura propuesta en Metabase | Fuente |
| --- | --- | --- |
| RF1 Resumen ejecutivo | KPIs principales, ingresos por categoria, estado de entregas, metodos de pago y dispositivos. | `mart_sales_summary`, `mart_sales_by_category`, `mart_logistics`, `mart_payment_methods`, `mart_ventas_dispositivo`, `mart_period_variation` |
| RF2 Filtros globales | Filtros de fecha, categoria, ciudad, dispositivo y metodo de pago conectados a las preguntas del tablero. | `analytics.fact_orders` |
| RF3 Analisis de ventas | Evolucion mensual, ventas por categoria/marca, ventas por dispositivo y variacion mensual. | `mart_ventas_mensuales`, `mart_sales_by_category`, `mart_sales_by_brand`, `mart_ventas_dispositivo`, `mart_period_variation` |
| RF4 Analisis logistico | Estado de entrega, tiempo promedio por ciudad, tasa de devolucion y tendencia de demoras. | `mart_logistics`, `mart_logistica_ciudad`, `mart_returns`, `mart_demoras_mensuales` |
| RF5 Experiencia del cliente | Rating por categoria, satisfaccion por ciudad, relacion rating/devolucion/envio. | `mart_customer_experience`, `mart_satisfaccion_ciudad` |
| RF6 Analisis de vendedores | Ranking por ingresos, ordenes, rating y devoluciones. | `mart_seller_performance` |
| RF7 Exportacion CSV | Usar la accion de descarga de resultados de Metabase en cada pregunta o tabla. | Funcionalidad nativa de Metabase |
| RF8 Navegacion entre paginas | Crear una coleccion o dashboard con pestanas/secciones: Resumen, Ventas, Logistica, Clientes, Vendedores. | Configuracion Metabase |
| RF9 Tutorial y glosario | Documento de formulas e interpretacion de KPIs. | `docs/glosario_kpis.md` |
| RF10 Ingesta de archivos | DAG programado cada 5 minutos y validacion de disponibilidad de CSV. | `dags/amazon_pipeline.py` |
| RF11 Validacion de estructura | Validacion de columnas, tipos, fechas, rangos y valores permitidos. | `scripts/validation/validate_csv.py` |
| RF12 Procesamiento automatizado | Flujo Airflow: validacion, staging, limpieza, fact table y marts. | `dags/amazon_pipeline.py` |
| RF13 Notificacion de estado | Tarea de notificacion y auditoria de exito/fallo. | `scripts/utils/notify_status.py`, `scripts/utils/audit.py` |
| RF14 Persistencia historica | Carga append en staging/fact y control de archivos procesados. | `scripts/load/load_staging.py`, `scripts/transform/clean_staging.py`, `scripts/utils/register_processed_file.py` |

## Checklist De Construccion En Metabase

1. Conectar Metabase a `postgres-dwh`.
2. Crear una coleccion llamada `Amazon E-Commerce`.
3. Crear dashboards: `Resumen`, `Ventas`, `Logistica`, `Clientes`, `Vendedores`.
4. Agregar filtros globales de fecha, categoria, ciudad, dispositivo y metodo de pago.
5. Crear preguntas basadas en los marts listados en la matriz y en `docs/metabase_preguntas_dashboards.md`.
6. Validar que cada pregunta permita descarga CSV.
7. Tomar capturas del dashboard final para anexarlas a la entrega.

## Preguntas SQL Documentadas

Las preguntas SQL listas para cargar en Metabase estan en
`docs/metabase_preguntas_dashboards.md`. Ese documento tambien incluye las
visualizaciones faltantes del diagnostico: descuento vs ordenes, distribucion de
rating, metodo de pago vs devolucion y demora vs devolucion.
