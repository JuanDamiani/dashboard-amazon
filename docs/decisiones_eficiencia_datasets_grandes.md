# Decisiones de eficiencia para datasets grandes

Este documento explica las decisiones tecnicas tomadas para que el pipeline pueda procesar archivos CSV grandes, incluyendo datasets de mas de 1 millon de filas, sin depender de cargas completas en memoria dentro de Airflow.

## Contexto

El proyecto procesa archivos CSV de e-commerce y los transforma en datos analiticos disponibles para Metabase. En las primeras versiones, el flujo funcionaba correctamente con archivos chicos, pero al probar un CSV de 1.000.000 de filas aparecieron problemas de rendimiento y estabilidad:

- alto consumo de memoria;
- tareas de Airflow marcadas como zombie;
- procesos terminados con `return code -9`;
- demoras excesivas al insertar datos;
- transformaciones pandas poco adecuadas para volumenes grandes.

Por eso se refactorizaron las etapas principales del ETL:

```text
validate_csv -> load_staging -> clean_staging -> KPIs
```

El objetivo fue que Airflow orqueste el proceso, mientras PostgreSQL realiza la carga y transformacion pesada.

## Decision general

La decision principal fue cambiar de un enfoque centrado en pandas a un enfoque centrado en PostgreSQL:

```text
CSV
-> validacion por chunks
-> staging tabular
-> transformacion SQL
-> fact_orders
-> marts
```

Esto mejora la escalabilidad porque evita mantener todo el dataset en memoria y aprovecha el motor de base de datos para operaciones masivas.

## Cambios en validate_csv

### Problema anterior

La validacion original leia el CSV completo en un unico DataFrame:

```text
CSV completo -> pandas DataFrame -> validaciones
```

Esto era aceptable para archivos chicos, pero con 1.000.000 de filas implicaba:

- alto uso de memoria;
- mayor riesgo de que Airflow pierda heartbeat;
- validacion poco escalable;
- dificultad para procesar archivos aun mas grandes.

### Decision tomada

`validate_csv` fue modificado para validar por chunks. Ahora lee por partes usando `LOAD_CHUNK_SIZE` y acumula conteos de errores y advertencias.

La validacion sigue revisando:

- columnas requeridas;
- nulos en columnas criticas;
- columnas numericas;
- formato de fechas;
- valores estrictos permitidos;
- rangos validos;
- valores sospechosos o nuevos.

### Justificacion

Validar por chunks permite revisar archivos grandes sin cargar todo el archivo en memoria. Airflow solo mantiene un fragmento del CSV por vez.

Esto es especialmente importante para RF11 del SRS, porque el sistema debe validar automaticamente la estructura del archivo antes de procesarlo, pero esa validacion debe seguir siendo viable con datasets grandes.

### Resultado esperado

Con este cambio:

- el uso de memoria es mas estable;
- el pipeline puede validar archivos grandes;
- los errores se resumen por archivo;
- se guarda un registro en `analytics.validation_summary`;
- el DAG puede fallar temprano si el archivo no cumple la estructura.

## Cambios en load_staging

### Problema anterior

La version previa de `load_staging` tenia dos problemas importantes.

Primero, convertia cada fila del CSV en JSONB desde Python:

```text
CSV -> pandas DataFrame -> lista de diccionarios -> DataFrame JSONB -> PostgreSQL
```

Para 1.000.000 de filas, esto multiplicaba el uso de memoria.

Segundo, usaba `pandas.to_sql`, que funciona pero no es la forma mas eficiente de insertar grandes volumenes en PostgreSQL.

### Decision tomada

Se reemplazo la carga JSONB por una staging tabular:

```text
staging.amazon_sales_input
```

Esta tabla tiene columnas equivalentes a las del CSV, mas metadatos:

- `source_file`;
- `batch_id`;
- `loaded_at`.

Ademas, la carga ahora usa `COPY` de PostgreSQL en lugar de `to_sql`.

El flujo actual es:

```text
CSV por chunks
-> preparar columnas tabulares
-> COPY a staging.amazon_sales_input
-> ANALYZE staging.amazon_sales_input
```

### Justificacion

PostgreSQL `COPY` esta disenado para cargas masivas y suele ser mucho mas rapido que ejecutar muchos inserts generados por pandas.

La staging tabular tambien simplifica las transformaciones posteriores, porque PostgreSQL puede operar directamente sobre columnas reales en lugar de parsear JSONB fila por fila.

Esto mejora RF10 y RF12:

- RF10: permite incorporar nuevos CSV de forma automatizada;
- RF12: prepara los datos para el procesamiento ETL automatizado.

Tambien mejora RNF-10, porque separa mejor las responsabilidades:

- `load_staging` carga datos;
- `clean_staging` transforma datos;
- los KPI scripts agregan metricas.

### Decision sobre deduplicacion

Se quito la deduplicacion en Python.

Antes, `load_staging` mantenia un conjunto `seen_keys` para evitar duplicados durante la carga. Para datasets grandes, ese conjunto puede crecer mucho y consumir memoria.

La deduplicacion ahora se hace en SQL dentro de `clean_staging`, usando:

```sql
ROW_NUMBER() OVER (PARTITION BY sale_id ORDER BY sale_id)
```

y luego:

```sql
ON CONFLICT (sale_id) DO NOTHING
```

Esto delega la deduplicacion al motor de base de datos.

### Resultado esperado

Con este cambio:

- la carga de archivos grandes es mas rapida;
- el consumo de memoria baja;
- PostgreSQL recibe datos en una estructura mas eficiente;
- se preserva trazabilidad por `batch_id`;
- se actualizan estadisticas con `ANALYZE` para mejorar consultas posteriores.

## Cambios en clean_staging

### Problema anterior

La version anterior de `clean_staging` leia los datos desde staging hacia pandas:

```text
staging -> pandas DataFrame -> transformaciones -> fact_orders
```

Esto volvia a cargar el batch completo en memoria. Para 1.000.000 de filas, era otro punto critico de consumo de recursos.

Ademas, al usar JSONB como staging principal, era necesario parsear payloads fila por fila.

### Decision tomada

`clean_staging` fue refactorizado para transformar con SQL dentro de PostgreSQL.

Ahora ejecuta una consulta del tipo:

```sql
INSERT INTO analytics.fact_orders (...)
SELECT ...
FROM staging.amazon_sales_input
WHERE batch_id = :batch_id
ON CONFLICT (sale_id) DO NOTHING;
```

La transformacion SQL realiza:

- generacion de `sale_id`;
- parseo de fechas;
- conversion de tipos numericos;
- normalizacion de textos;
- conversion de booleanos;
- deduplicacion por `sale_id`;
- insercion idempotente en `fact_orders`.

### Parseo de fechas

Se agrego soporte para formatos distintos de fecha, porque los datasets pueden venir con:

```text
YYYY-MM-DD
D/M/YYYY
DD/MM/YYYY
```

La transformacion usa un `CASE` para detectar el formato antes de aplicar `to_date`.

Esto evita errores como:

```text
date/time field value out of range
```

### Justificacion

PostgreSQL es mas adecuado que pandas para transformar millones de filas ya cargadas en base. El motor puede optimizar consultas, usar indices y evitar transferir grandes volumenes de datos hacia el proceso de Airflow.

Esto refuerza RF12 y RF14:

- RF12: limpieza, transformacion y carga automatizada;
- RF14: persistencia historica sin duplicar informacion previa.

### Resultado esperado

Con este cambio:

- Airflow no carga el batch completo en memoria;
- la transformacion es mas estable;
- la carga a `fact_orders` es idempotente;
- se evitan duplicados por `sale_id`;
- se actualizan estadisticas con `ANALYZE analytics.fact_orders`.

## Auditoria y trazabilidad

Tambien se mejoro la auditoria para datasets grandes.

La tabla `analytics.etl_audit_log` registra:

- archivo procesado;
- `batch_id`;
- filas leidas;
- filas cargadas;
- filas rechazadas;
- estado final;
- mensaje.

La tabla `analytics.validation_summary` registra:

- archivo;
- hash;
- filas validadas;
- cantidad de errores;
- cantidad de advertencias;
- estado de validacion.

Esto permite demostrar que el pipeline proceso correctamente un archivo grande y deja evidencia para soporte y debugging.

## Ciclo de archivos

El pipeline tambien mueve archivos segun el resultado:

```text
data/input     -> archivos pendientes
data/processed -> archivos procesados correctamente
data/rejected  -> archivos fallidos
```

Esto evita reprocesos accidentales y permite procesar multiples CSV pendientes, uno por corrida.

## Beneficios obtenidos

Con estas decisiones, el pipeline queda mejor preparado para volumenes grandes:

- menor uso de memoria en Airflow;
- carga mas rapida mediante PostgreSQL `COPY`;
- transformacion mas eficiente con SQL;
- deduplicacion centralizada en base de datos;
- soporte para formatos de fecha distintos;
- auditoria completa por batch;
- mejor trazabilidad de archivos;
- mayor alineacion con RF10, RF11, RF12, RF13, RF14 y RNF-10 del SRS.

## Limitaciones actuales

Aunque el pipeline ya procesa datasets grandes, todavia existen posibles mejoras:

- usar tablas particionadas por fecha si el volumen crece mucho mas;
- recalcular marts de forma incremental en lugar de borrar y recalcular todo;
- usar `COPY` directamente desde archivo si se quiere evitar el buffer intermedio;
- agregar metricas de duracion por etapa;
- crear indices compuestos si las transformaciones o consultas lo requieren;
- separar validaciones criticas de validaciones exploratorias para acelerar la ingesta.

## Resumen

La decision mas importante fue mover el trabajo pesado fuera de pandas y hacia PostgreSQL.

Airflow queda como orquestador del proceso, pandas se usa solo para leer chunks del CSV, y PostgreSQL se encarga de cargar, transformar, deduplicar y preparar los datos analiticos.

Este enfoque es mas adecuado para el alcance del SRS y para datasets de mas de 1 millon de filas.
