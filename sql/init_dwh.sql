-- =========================================================
-- AMAZON E-COMMERCE DASHBOARD
-- DATA WAREHOUSE INITIALIZATION
-- =========================================================
-- Arquitectura:
--
-- CSV INPUT
--     ↓
-- RAW STAGING
--     ↓
-- FACT TABLE
--     ↓
-- ANALYTICS MARTS
--     ↓
-- METABASE
--
-- Objetivos:
-- - Persistencia histórica
-- - Evitar duplicados
-- - Reprocesamiento seguro
-- - Observabilidad ETL
-- - Optimización para dashboards
-- - Alineación con SRS y Airflow
-- =========================================================

-- =========================================================
-- SCHEMAS
-- =========================================================

CREATE SCHEMA IF NOT EXISTS staging;
CREATE SCHEMA IF NOT EXISTS analytics;

-- =========================================================
-- RAW STAGING
-- =========================================================
-- Guarda el CSV original sin transformar.
-- Permite:
-- - auditoría
-- - reprocesamiento
-- - debugging
-- - trazabilidad
-- =========================================================

CREATE TABLE IF NOT EXISTS staging.amazon_sales_raw (

    raw_id SERIAL PRIMARY KEY,

    source_file VARCHAR(255) NOT NULL,

    batch_id VARCHAR(100) NOT NULL,

    loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    raw_payload JSONB NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_raw_batch
ON staging.amazon_sales_raw(batch_id);

CREATE INDEX IF NOT EXISTS idx_raw_loaded_at
ON staging.amazon_sales_raw(loaded_at);

-- =========================================================
-- TABULAR STAGING
-- =========================================================
-- Tabla staging principal para archivos grandes.
-- A diferencia de amazon_sales_raw, evita JSONB masivo y permite transformar
-- hacia fact_orders con SQL dentro de PostgreSQL.
-- =========================================================

CREATE TABLE IF NOT EXISTS staging.amazon_sales_input (

    staging_id BIGSERIAL PRIMARY KEY,

    source_file VARCHAR(255) NOT NULL,

    batch_id VARCHAR(100) NOT NULL,

    loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    user_id TEXT,

    product_id TEXT,

    category TEXT,

    subcategory TEXT,

    brand TEXT,

    price TEXT,

    discount TEXT,

    final_price TEXT,

    rating TEXT,

    review_count TEXT,

    stock TEXT,

    seller_id TEXT,

    seller_rating TEXT,

    purchase_date TEXT,

    shipping_time_days TEXT,

    location TEXT,

    device TEXT,

    payment_method TEXT,

    is_returned TEXT,

    delivery_status TEXT
);

CREATE INDEX IF NOT EXISTS idx_input_batch
ON staging.amazon_sales_input(batch_id);

CREATE INDEX IF NOT EXISTS idx_input_file
ON staging.amazon_sales_input(source_file);

-- =========================================================
-- PROCESSED FILES
-- =========================================================
-- Evita reprocesamiento de archivos CSV.
-- Importante para persistencia histórica.
-- RF14
-- =========================================================

CREATE TABLE IF NOT EXISTS analytics.processed_files (

    id SERIAL PRIMARY KEY,

    file_name VARCHAR(255) NOT NULL,

    file_hash VARCHAR(64),

    batch_id VARCHAR(100),

    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_processed_files_name_hash
ON analytics.processed_files(file_name, file_hash);

-- =========================================================
-- FACT TABLE
-- =========================================================
-- Tabla central del DWH.
-- 1 fila = 1 orden procesada.
-- Todas las métricas salen desde acá.
-- =========================================================

CREATE TABLE IF NOT EXISTS analytics.fact_orders (

    fact_id SERIAL PRIMARY KEY,

    sale_id VARCHAR(255) UNIQUE NOT NULL,

    batch_id VARCHAR(100),

    source_file VARCHAR(255),

    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- FECHAS

    purchase_timestamp TIMESTAMP,

    purchase_date DATE,

    purchase_year INTEGER,

    purchase_month INTEGER,

    purchase_day INTEGER,

    -- ENTIDADES

    user_id VARCHAR(50),

    product_id VARCHAR(50),

    seller_id VARCHAR(50),

    -- PRODUCTO

    category VARCHAR(100),

    subcategory VARCHAR(100),

    brand VARCHAR(100),

    -- UBICACIÓN Y CANAL

    location VARCHAR(100),

    device VARCHAR(50),

    payment_method VARCHAR(50),

    delivery_status VARCHAR(50),

    -- MÉTRICAS

    price NUMERIC(12,2),

    discount NUMERIC(5,2),

    final_price NUMERIC(12,2),

    rating NUMERIC(3,2),

    review_count INTEGER,

    seller_rating NUMERIC(3,2),

    shipping_time_days INTEGER,

    stock INTEGER,

    is_returned BOOLEAN
);

-- =========================================================
-- FACT INDEXES
-- =========================================================

CREATE INDEX IF NOT EXISTS idx_fact_purchase_date
ON analytics.fact_orders(purchase_date);

CREATE INDEX IF NOT EXISTS idx_fact_category
ON analytics.fact_orders(category);

CREATE INDEX IF NOT EXISTS idx_fact_subcategory
ON analytics.fact_orders(subcategory);

CREATE INDEX IF NOT EXISTS idx_fact_brand
ON analytics.fact_orders(brand);

CREATE INDEX IF NOT EXISTS idx_fact_seller
ON analytics.fact_orders(seller_id);

CREATE INDEX IF NOT EXISTS idx_fact_location
ON analytics.fact_orders(location);

CREATE INDEX IF NOT EXISTS idx_fact_device
ON analytics.fact_orders(device);

CREATE INDEX IF NOT EXISTS idx_fact_payment
ON analytics.fact_orders(payment_method);

CREATE INDEX IF NOT EXISTS idx_fact_delivery_status
ON analytics.fact_orders(delivery_status);

-- =========================================================
-- MART: EXECUTIVE SUMMARY (RF1)
-- =========================================================

CREATE TABLE IF NOT EXISTS analytics.mart_sales_summary (

    metric_date DATE PRIMARY KEY,

    total_orders INTEGER,

    total_revenue NUMERIC(14,2),

    avg_ticket NUMERIC(14,2),

    avg_product_rating NUMERIC(4,2),

    avg_seller_rating NUMERIC(4,2),

    avg_shipping_days NUMERIC(6,2),

    return_rate NUMERIC(6,2)
);

-- =========================================================
-- MART: SALES BY CATEGORY (RF3)
-- =========================================================

CREATE TABLE IF NOT EXISTS analytics.mart_sales_by_category (

    metric_date DATE,

    category VARCHAR(100),

    total_orders INTEGER,

    total_revenue NUMERIC(14,2),

    avg_rating NUMERIC(4,2),

    avg_discount NUMERIC(6,2)
);

CREATE INDEX IF NOT EXISTS idx_mart_category
ON analytics.mart_sales_by_category(category);

-- =========================================================
-- MART: SALES BY BRAND (RF3)
-- =========================================================

CREATE TABLE IF NOT EXISTS analytics.mart_sales_by_brand (

    metric_date DATE,

    brand VARCHAR(100),

    total_orders INTEGER,

    total_revenue NUMERIC(14,2),

    avg_rating NUMERIC(4,2),

    avg_seller_rating NUMERIC(4,2)
);

CREATE INDEX IF NOT EXISTS idx_mart_brand
ON analytics.mart_sales_by_brand(brand);

-- =========================================================
-- MART: VENTAS MENSUALES (RF3)
-- =========================================================

CREATE TABLE IF NOT EXISTS analytics.mart_ventas_mensuales (

    metric_date DATE,

    anio INTEGER,

    mes INTEGER,

    total_orders INTEGER,

    revenue NUMERIC(14,2),

    avg_ticket NUMERIC(14,2)
);

-- =========================================================
-- MART: VENTAS POR DISPOSITIVO (RF3, RF5)
-- =========================================================

CREATE TABLE IF NOT EXISTS analytics.mart_ventas_dispositivo (

    metric_date DATE,

    device VARCHAR(50),

    category VARCHAR(100),

    total_orders INTEGER,

    revenue NUMERIC(14,2)
);

-- =========================================================
-- MART: LOGISTICS (RF4)
-- =========================================================

CREATE TABLE IF NOT EXISTS analytics.mart_logistics (

    metric_date DATE,

    delivery_status VARCHAR(50),

    total_orders INTEGER,

    avg_shipping_days NUMERIC(6,2),

    return_rate NUMERIC(6,2)
);

-- =========================================================
-- MART: LOGISTICA POR CIUDAD (RF4)
-- =========================================================

CREATE TABLE IF NOT EXISTS analytics.mart_logistica_ciudad (

    metric_date DATE,

    location VARCHAR(100),

    avg_shipping_days NUMERIC(6,2),

    return_rate NUMERIC(6,2),

    total_orders INTEGER
);

-- =========================================================
-- MART: DEMORAS MENSUALES (RF4)
-- =========================================================

CREATE TABLE IF NOT EXISTS analytics.mart_demoras_mensuales (

    metric_date DATE,

    anio INTEGER,

    mes INTEGER,

    total_delayed INTEGER,

    total_orders INTEGER,

    pct_delayed NUMERIC(6,2)
);

-- =========================================================
-- MART: VARIACION RESPECTO AL PERIODO ANTERIOR (RF1, RF3)
-- =========================================================

CREATE TABLE IF NOT EXISTS analytics.mart_period_variation (

    metric_date DATE,

    period_month DATE,

    total_orders INTEGER,

    total_revenue NUMERIC(14,2),

    avg_ticket NUMERIC(14,2),

    return_rate NUMERIC(6,2),

    avg_product_rating NUMERIC(4,2),

    total_orders_pct_change NUMERIC(14,4),

    total_revenue_pct_change NUMERIC(14,4),

    avg_ticket_pct_change NUMERIC(14,4),

    return_rate_pct_change NUMERIC(14,4),

    avg_product_rating_pct_change NUMERIC(14,4)
);

CREATE INDEX IF NOT EXISTS idx_mart_period_variation_month
ON analytics.mart_period_variation(period_month);

-- =========================================================
-- MART: PAYMENT METHODS (RF1, RF7)
-- =========================================================

CREATE TABLE IF NOT EXISTS analytics.mart_payment_methods (

    metric_date DATE,

    payment_method VARCHAR(50),

    total_orders INTEGER,

    total_revenue NUMERIC(14,2),

    avg_ticket NUMERIC(14,2)
);

-- =========================================================
-- MART: RETURNS (RF4, RF5)
-- =========================================================

CREATE TABLE IF NOT EXISTS analytics.mart_returns (

    metric_date DATE,

    category VARCHAR(100),

    returned_orders INTEGER,

    total_orders INTEGER,

    return_rate NUMERIC(6,2)
);

-- =========================================================
-- MART: SELLER PERFORMANCE (RF6)
-- =========================================================

CREATE TABLE IF NOT EXISTS analytics.mart_seller_performance (

    metric_date DATE,

    seller_id VARCHAR(50),

    total_orders INTEGER,

    total_revenue NUMERIC(14,2),

    avg_seller_rating NUMERIC(4,2),

    return_rate NUMERIC(6,2)
);

CREATE INDEX IF NOT EXISTS idx_mart_seller
ON analytics.mart_seller_performance(seller_id);

-- =========================================================
-- MART: CUSTOMER EXPERIENCE (RF5)
-- =========================================================

CREATE TABLE IF NOT EXISTS analytics.mart_customer_experience (

    metric_date DATE,

    category VARCHAR(100),

    avg_rating NUMERIC(4,2),

    return_rate NUMERIC(6,2),

    avg_shipping_days NUMERIC(6,2)
);

-- =========================================================
-- MART: SATISFACCION POR CIUDAD (RF5)
-- =========================================================

CREATE TABLE IF NOT EXISTS analytics.mart_satisfaccion_ciudad (

    metric_date DATE,

    location VARCHAR(100),

    avg_rating NUMERIC(4,2),

    total_orders INTEGER,

    return_rate NUMERIC(6,2)
);

-- =========================================================
-- ETL AUDIT LOG (RF13)
-- =========================================================
-- Observabilidad y monitoreo ETL.
-- =========================================================

CREATE TABLE IF NOT EXISTS analytics.etl_audit_log (

    id SERIAL PRIMARY KEY,

    process_name VARCHAR(100),

    source_file VARCHAR(255),

    batch_id VARCHAR(100),

    rows_processed INTEGER,

    rows_read INTEGER,

    rows_loaded INTEGER,

    rows_rejected INTEGER,

    status VARCHAR(50),

    message TEXT,

    execution_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_audit_execution_time
ON analytics.etl_audit_log(execution_time);

CREATE INDEX IF NOT EXISTS idx_audit_status
ON analytics.etl_audit_log(status);

-- =========================================================
-- VALIDATION SUMMARY (RF11, RF13)
-- =========================================================

CREATE TABLE IF NOT EXISTS analytics.validation_summary (

    id SERIAL PRIMARY KEY,

    file_name VARCHAR(255),

    file_hash VARCHAR(64),

    rows_total INTEGER,

    error_count INTEGER,

    warning_count INTEGER,

    status VARCHAR(50),

    errors TEXT,

    warnings TEXT,

    validated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_validation_summary_file
ON analytics.validation_summary(file_name);



-- =========================================================
-- MART: DELIVERY PERFORMANCE (RF4)
-- % entregas a tiempo, % demorados, % en transito
-- =========================================================
 
CREATE TABLE IF NOT EXISTS analytics.mart_delivery_performance (
 
    metric_date         DATE,
 
    total_orders        INTEGER,
 
    delivered_orders    INTEGER,
 
    delayed_orders      INTEGER,
 
    in_transit_orders   INTEGER,
 
    returned_orders     INTEGER,
 
    pct_on_time         NUMERIC(6,2),
 
    pct_delayed         NUMERIC(6,2),
 
    pct_in_transit      NUMERIC(6,2),
 
    pct_returned        NUMERIC(6,2)
);
 
-- =========================================================
-- MART: PAYMENT VS RETURNS (RF4, RF5)
-- Relacion entre metodo de pago y tasa de devolucion
-- =========================================================
 
CREATE TABLE IF NOT EXISTS analytics.mart_payment_vs_returns (
 
    metric_date      DATE,
 
    payment_method   VARCHAR(50),
 
    total_orders     INTEGER,
 
    returned_orders  INTEGER,
 
    return_rate      NUMERIC(6,2)
);
 
-- =========================================================
-- MART: DELAYS VS RETURNS (RF4)
-- Relacion entre dias de envio y tasa de devolucion
-- =========================================================
 
CREATE TABLE IF NOT EXISTS analytics.mart_delays_vs_returns (
 
    metric_date         DATE,
 
    shipping_time_days  INTEGER,
 
    total_orders        INTEGER,
 
    returned_orders     INTEGER,
 
    return_rate         NUMERIC(6,2)
);
 
-- =========================================================
-- MART: RATING DISTRIBUTION (RF5)
-- Distribucion de ordenes por calificacion exacta
-- =========================================================
 
CREATE TABLE IF NOT EXISTS analytics.mart_rating_distribution (
 
    metric_date     DATE,
 
    rating          NUMERIC(3,2),
 
    total_orders    INTEGER,
 
    order_share_pct NUMERIC(6,2)
);
 
-- =========================================================
-- MART: RATING BY RANGE (RF5)
-- Distribucion de ordenes por rango de calificacion
-- =========================================================
 
CREATE TABLE IF NOT EXISTS analytics.mart_rating_by_range (
 
    metric_date     DATE,
 
    rating_range    VARCHAR(20),
 
    total_orders    INTEGER,
 
    order_share_pct NUMERIC(6,2),
 
    avg_rating      NUMERIC(4,2),
 
    return_rate     NUMERIC(6,2)
);
 
-- =========================================================
-- MART: CATEGORIES BY SELLER (RF6)
-- Categorias comercializadas por vendedor
-- =========================================================
 
CREATE TABLE IF NOT EXISTS analytics.mart_categories_by_seller (
 
    metric_date    DATE,
 
    seller_id      VARCHAR(50),
 
    category       VARCHAR(100),
 
    total_orders   INTEGER,
 
    total_revenue  NUMERIC(14,2),
 
    return_rate    NUMERIC(6,2)
);
 
-- =========================================================
-- MART: DISCOUNT VS ORDERS (RF3)
-- Relacion entre nivel de descuento y volumen de ordenes
-- =========================================================
 
CREATE TABLE IF NOT EXISTS analytics.mart_discount_vs_orders (
 
    metric_date     DATE,
 
    discount_range  VARCHAR(20),
 
    total_orders    INTEGER,
 
    total_revenue   NUMERIC(14,2),
 
    avg_ticket      NUMERIC(14,2)
);

-- =========================================================
-- FUTURAS EXTENSIONES
-- =========================================================
--
-- Posibles mejoras:
--
-- - Slowly Changing Dimensions (SCD)
-- - Dimensiones separadas:
--     dim_products
--     dim_sellers
--     dim_customers
--     dim_dates
--
-- - Particionamiento por fecha
-- - Materialized views
-- - Incremental loading
-- - Alertas automáticas Airflow
-- - Data quality scoring
--
-- =========================================================
