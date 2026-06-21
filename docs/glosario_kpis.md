# Glosario de KPIs

Este documento cubre RF9: definicion, formula e interpretacion de los KPIs usados en el dashboard.

| KPI | Formula | Interpretacion | Fuente sugerida |
| --- | --- | --- | --- |
| Ingresos totales | `SUM(final_price)` | Monto total vendido en el periodo filtrado. | `analytics.fact_orders`, `mart_sales_summary` |
| Ordenes procesadas | `COUNT(*)` | Cantidad de compras registradas. | `analytics.fact_orders`, `mart_sales_summary` |
| Ticket promedio | `AVG(final_price)` | Valor promedio por orden. | `mart_sales_summary`, `mart_period_variation` |
| Tasa de devolucion | `AVG(CASE WHEN is_returned THEN 1 ELSE 0 END) * 100` | Porcentaje de ordenes devueltas. | `mart_sales_summary`, `mart_returns` |
| Rating promedio de producto | `AVG(rating)` | Satisfaccion promedio asociada al producto. | `mart_sales_summary`, `mart_customer_experience` |
| Rating promedio de vendedor | `AVG(seller_rating)` | Desempeno promedio de vendedores. | `mart_sales_summary`, `mart_seller_performance` |
| Tiempo promedio de envio | `AVG(shipping_time_days)` | Duracion promedio entre compra y entrega. | `mart_logistics`, `mart_logistica_ciudad` |
| Pedidos demorados | `SUM(CASE WHEN delivery_status = 'Delayed' THEN 1 ELSE 0 END)` | Cantidad de ordenes con demora. | `mart_demoras_mensuales` |
| Porcentaje de pedidos demorados | `AVG(CASE WHEN delivery_status = 'Delayed' THEN 1 ELSE 0 END) * 100` | Peso de los pedidos demorados sobre el total. | `mart_demoras_mensuales` |
| Variacion porcentual | `(valor_actual - valor_anterior) / valor_anterior * 100` | Cambio frente al periodo mensual anterior. | `mart_period_variation` |

## Filtros Globales

Los filtros globales del SRS se aplican desde Streamlit usando campos de
`analytics.fact_orders`:

- Fecha: `purchase_date`
- Categoria: `category`
- Ciudad: `location`
- Dispositivo: `device`
- Metodo de pago: `payment_method`
