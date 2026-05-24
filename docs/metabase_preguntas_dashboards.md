# Preguntas Y Dashboards En Metabase

Este documento deja preparadas las preguntas SQL y la organizacion de dashboards
necesarias para cubrir RF1 a RF8 del SRS. La base recomendada en Metabase es
PostgreSQL `amazon_dwh`, esquema `analytics`.

## Estado De Metabase

Metabase esta disponible en `http://localhost:3000`.

Si al ingresar aparece el asistente inicial, primero conectar la base:

| Campo | Valor |
| --- | --- |
| Tipo | PostgreSQL |
| Host | `postgres-dwh` |
| Puerto | `5432` |
| Base | `amazon_dwh` |
| Usuario | `dwh` |
| Password | `dwh123` |
| Esquema principal | `analytics` |

En este entorno local ya se creo la coleccion `Amazon E-Commerce`, conectada a
la base `Amazon DWH`.

| Dashboard | URL local | Requisitos cubiertos |
| --- | --- | --- |
| Resumen | `http://localhost:3000/dashboard/2` | RF1, RF2, RF7, RF8 |
| Ventas | `http://localhost:3000/dashboard/3` | RF2, RF3, RF7, RF8 |
| Logistica | `http://localhost:3000/dashboard/4` | RF2, RF4, RF7, RF8 |
| Clientes | `http://localhost:3000/dashboard/5` | RF2, RF5, RF7, RF8 |
| Vendedores | `http://localhost:3000/dashboard/6` | RF2, RF6, RF7, RF8 |

## Filtros Globales Sugeridos

Crear estos filtros en cada dashboard y conectarlos a las preguntas que usen
`analytics.fact_orders` o una consulta basada en sus campos:

| Filtro | Tipo en Metabase | Campo |
| --- | --- | --- |
| Fecha de compra | Date | `purchase_date` |
| Categoria | Category | `category` |
| Ciudad | Category | `location` |
| Dispositivo | Category | `device` |
| Metodo de pago | Category | `payment_method` |

En preguntas SQL nativas, usar variables de tipo Field Filter cuando sea posible.
Para consultas agregadas sobre marts, los filtros se pueden aplicar creando la
pregunta directamente desde `analytics.fact_orders` o usando una version SQL con
variables.

Los dashboards creados en este entorno usan preguntas SQL nativas basadas en
`analytics.fact_orders` con variables Field Filter, por lo que los cinco filtros
globales quedan conectados a cada tarjeta.

Ejemplo base con filtros opcionales:

```sql
SELECT
    category,
    COUNT(*) AS total_orders,
    SUM(final_price) AS total_revenue
FROM analytics.fact_orders
WHERE 1 = 1
[[AND {{purchase_date}}]]
[[AND {{category}}]]
[[AND {{location}}]]
[[AND {{device}}]]
[[AND {{payment_method}}]]
GROUP BY category
ORDER BY total_revenue DESC;
```

## Dashboard Resumen

Cubre RF1, RF2, RF7 y RF8. Debe mostrar el estado general del negocio y permitir
filtrar por fecha, categoria, ciudad, dispositivo y metodo de pago.

### KPI General

Visualizacion: tabla de una fila o indicadores.

```sql
SELECT
    total_orders,
    total_revenue,
    avg_ticket,
    avg_product_rating,
    avg_seller_rating,
    avg_shipping_days,
    return_rate
FROM analytics.mart_sales_summary;
```

### Variacion Mensual Reciente

Visualizacion: tabla o indicadores con variacion porcentual.

```sql
SELECT
    period_month,
    total_orders,
    total_orders_variation_pct,
    total_revenue,
    total_revenue_variation_pct,
    avg_ticket,
    avg_ticket_variation_pct
FROM analytics.mart_period_variation
ORDER BY period_month DESC
LIMIT 12;
```

### Ingresos Por Categoria

Visualizacion: barras.

```sql
SELECT
    category,
    total_orders,
    total_revenue,
    avg_ticket,
    avg_rating,
    avg_discount
FROM analytics.mart_sales_by_category
ORDER BY total_revenue DESC;
```

### Estado De Entregas

Visualizacion: torta o barras.

```sql
SELECT
    delivery_status,
    total_orders,
    avg_shipping_days,
    return_rate
FROM analytics.mart_logistics
ORDER BY total_orders DESC;
```

### Metodo De Pago

Visualizacion: barras o tabla exportable.

```sql
SELECT
    payment_method,
    total_orders,
    total_revenue,
    avg_ticket
FROM analytics.mart_payment_methods
ORDER BY total_revenue DESC;
```

## Dashboard Ventas

Cubre RF2, RF3, RF7 y RF8. Debe concentrar evolucion temporal, categorias,
marcas, dispositivos y efecto de descuentos.

### Evolucion Mensual De Ventas

Visualizacion: linea.

```sql
SELECT
    MAKE_DATE(anio, mes, 1) AS period_month,
    total_orders,
    revenue,
    avg_ticket
FROM analytics.mart_ventas_mensuales
ORDER BY period_month;
```

### Ventas Por Marca

Visualizacion: barras horizontales o tabla con top N.

```sql
SELECT
    brand,
    total_orders,
    total_revenue,
    avg_ticket,
    avg_rating,
    avg_seller_rating
FROM analytics.mart_sales_by_brand
ORDER BY total_revenue DESC
LIMIT 25;
```

### Ventas Por Dispositivo Y Categoria

Visualizacion: barras apiladas o tabla dinamica.

```sql
SELECT
    device,
    category,
    total_orders,
    revenue,
    avg_ticket
FROM analytics.mart_ventas_dispositivo
ORDER BY device, revenue DESC;
```

### Descuento Vs Ordenes

Visualizacion: barras por rango de descuento. Esta pregunta cubre una
visualizacion faltante del diagnostico.

```sql
SELECT
    CASE
        WHEN discount < 10 THEN '00-09%'
        WHEN discount < 20 THEN '10-19%'
        WHEN discount < 30 THEN '20-29%'
        WHEN discount < 40 THEN '30-39%'
        WHEN discount < 50 THEN '40-49%'
        WHEN discount < 60 THEN '50-59%'
        WHEN discount < 70 THEN '60-69%'
        WHEN discount < 80 THEN '70-79%'
        WHEN discount < 90 THEN '80-89%'
        ELSE '90-100%'
    END AS discount_range,
    COUNT(*) AS total_orders,
    SUM(final_price) AS total_revenue,
    AVG(final_price) AS avg_ticket
FROM analytics.fact_orders
GROUP BY discount_range
ORDER BY discount_range;
```

## Dashboard Logistica

Cubre RF2, RF4, RF7 y RF8. Debe mostrar estados de entrega, demoras, tiempos de
envio y relacion entre logistica y devoluciones.

### Tiempo Promedio Por Ciudad

Visualizacion: barras o mapa si Metabase reconoce ciudades.

```sql
SELECT
    location,
    total_orders,
    avg_shipping_days,
    return_rate
FROM analytics.mart_logistica_ciudad
ORDER BY avg_shipping_days DESC;
```

### Demoras Mensuales

Visualizacion: linea.

```sql
SELECT
    MAKE_DATE(anio, mes, 1) AS period_month,
    delayed_orders,
    total_orders,
    delayed_rate
FROM analytics.mart_demoras_mensuales
ORDER BY period_month;
```

### Devoluciones Por Categoria

Visualizacion: barras.

```sql
SELECT
    category,
    returned_orders,
    total_orders,
    return_rate
FROM analytics.mart_returns
ORDER BY return_rate DESC;
```

### Demora Vs Devolucion

Visualizacion: barras comparando tasa de devolucion por dias de envio. Esta
pregunta cubre una visualizacion faltante del diagnostico.

```sql
SELECT
    shipping_time_days,
    COUNT(*) AS total_orders,
    SUM(CASE WHEN is_returned THEN 1 ELSE 0 END) AS returned_orders,
    ROUND(AVG(CASE WHEN is_returned THEN 1.0 ELSE 0.0 END) * 100, 2) AS return_rate
FROM analytics.fact_orders
GROUP BY shipping_time_days
ORDER BY shipping_time_days;
```

## Dashboard Clientes

Cubre RF2, RF5, RF7 y RF8. Debe mostrar satisfaccion, rating, devoluciones y
comportamiento por canal.

### Rating Por Categoria

Visualizacion: barras.

```sql
SELECT
    category,
    avg_rating,
    return_rate,
    avg_shipping_days,
    total_orders
FROM analytics.mart_customer_experience
ORDER BY avg_rating DESC;
```

### Satisfaccion Por Ciudad

Visualizacion: barras o mapa.

```sql
SELECT
    location,
    avg_rating,
    total_orders,
    return_rate
FROM analytics.mart_satisfaccion_ciudad
ORDER BY avg_rating DESC;
```

### Distribucion De Ratings

Visualizacion: histograma o barras. Esta pregunta cubre una visualizacion
faltante del diagnostico.

```sql
SELECT
    rating,
    COUNT(*) AS total_orders,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) AS order_share_pct
FROM analytics.fact_orders
GROUP BY rating
ORDER BY rating;
```

### Metodo De Pago Vs Devolucion

Visualizacion: barras. Esta pregunta cubre una visualizacion faltante del
diagnostico.

```sql
SELECT
    payment_method,
    COUNT(*) AS total_orders,
    SUM(CASE WHEN is_returned THEN 1 ELSE 0 END) AS returned_orders,
    ROUND(AVG(CASE WHEN is_returned THEN 1.0 ELSE 0.0 END) * 100, 2) AS return_rate
FROM analytics.fact_orders
GROUP BY payment_method
ORDER BY return_rate DESC;
```

## Dashboard Vendedores

Cubre RF2, RF6, RF7 y RF8. Debe permitir detectar vendedores con mayor volumen,
mejor rating y mayor tasa de devolucion.

### Ranking De Vendedores

Visualizacion: tabla.

```sql
SELECT
    seller_id,
    total_orders,
    total_revenue,
    avg_ticket,
    avg_seller_rating,
    return_rate
FROM analytics.mart_seller_performance
ORDER BY total_revenue DESC
LIMIT 100;
```

### Vendedores Con Mayor Tasa De Devolucion

Visualizacion: tabla.

```sql
SELECT
    seller_id,
    total_orders,
    total_revenue,
    avg_seller_rating,
    return_rate
FROM analytics.mart_seller_performance
WHERE total_orders >= 10
ORDER BY return_rate DESC, total_orders DESC
LIMIT 100;
```

### Rating De Vendedor Vs Ingresos

Visualizacion: dispersion.

```sql
SELECT
    seller_id,
    total_orders,
    total_revenue,
    avg_seller_rating,
    return_rate
FROM analytics.mart_seller_performance
WHERE total_orders >= 10
ORDER BY total_revenue DESC;
```

## Evidencia Para La Entrega

Para cerrar RF1 a RF8, capturar:

1. Pantalla de cada dashboard: Resumen, Ventas, Logistica, Clientes y Vendedores.
2. Una captura donde se vean los filtros globales configurados.
3. Una captura de una pregunta exportada como CSV desde Metabase para evidenciar RF7.
4. Una captura de la coleccion o navegacion entre dashboards para evidenciar RF8.
5. Este documento como anexo de preguntas SQL exportables/documentadas.
