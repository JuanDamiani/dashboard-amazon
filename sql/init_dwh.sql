CREATE SCHEMA IF NOT EXISTS staging;
CREATE SCHEMA IF NOT EXISTS analytics;

CREATE TABLE IF NOT EXISTS staging.amazon_sales_raw (

    user_id VARCHAR(50),
    product_id VARCHAR(50),

    category VARCHAR(100),
    subcategory VARCHAR(100),
    brand VARCHAR(100),

    price NUMERIC(12,2),
    discount NUMERIC(5,2),
    final_price NUMERIC(12,2),

    rating NUMERIC(3,2),
    review_count INTEGER,

    stock INTEGER,

    seller_id VARCHAR(50),
    seller_rating NUMERIC(3,2),

    purchase_date DATE,

    shipping_time_days INTEGER,

    location VARCHAR(100),
    device VARCHAR(50),
    payment_method VARCHAR(50),

    is_returned BOOLEAN,

    delivery_status VARCHAR(50)
);

CREATE TABLE IF NOT EXISTS analytics.kpi_sales_summary (

    metric_date DATE,

    total_orders INTEGER,

    total_revenue NUMERIC(14,2),

    avg_ticket NUMERIC(14,2),

    avg_product_rating NUMERIC(4,2),

    avg_seller_rating NUMERIC(4,2),

    avg_shipping_days NUMERIC(6,2),

    return_rate NUMERIC(6,2)
);

CREATE TABLE IF NOT EXISTS analytics.etl_audit_log (

    id SERIAL PRIMARY KEY,

    process_name VARCHAR(100),

    source_file VARCHAR(255),

    rows_processed INTEGER,

    status VARCHAR(50),

    message TEXT,

    execution_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
-- ==========================================
-- KPI TOP CATEGORIES
-- ==========================================

CREATE TABLE IF NOT EXISTS analytics.kpi_top_categories (

    category VARCHAR(100),

    total_orders INTEGER,

    revenue NUMERIC(14,2),

    avg_rating NUMERIC(4,2),

    avg_discount NUMERIC(6,2)
);

-- ==========================================
-- KPI TOP BRANDS
-- ==========================================

CREATE TABLE IF NOT EXISTS analytics.kpi_top_brands (

    brand VARCHAR(100),

    total_sales INTEGER,

    revenue NUMERIC(14,2),

    avg_rating NUMERIC(4,2),

    avg_seller_rating NUMERIC(4,2)
);

-- ==========================================
-- KPI DELIVERY METRICS
-- ==========================================

CREATE TABLE IF NOT EXISTS analytics.kpi_delivery_metrics (

    delivery_status VARCHAR(50),

    total_orders INTEGER,

    avg_shipping_days NUMERIC(6,2),

    return_rate NUMERIC(6,2)
);

-- ==========================================
-- KPI PAYMENT METHODS
-- ==========================================

CREATE TABLE IF NOT EXISTS analytics.kpi_payment_methods (

    payment_method VARCHAR(50),

    total_orders INTEGER,

    revenue NUMERIC(14,2),

    avg_ticket NUMERIC(14,2)
);

-- ==========================================
-- KPI RETURNS
-- ==========================================

CREATE TABLE IF NOT EXISTS analytics.kpi_returns (

    category VARCHAR(100),

    returned_orders INTEGER,

    total_orders INTEGER,

    return_rate NUMERIC(6,2)
);


-- ==========================================
-- SILVER - DATOS LIMPIOS
-- ==========================================
CREATE TABLE IF NOT EXISTS staging.amazon_sales_clean (
    user_id             VARCHAR(50),
    product_id          VARCHAR(50),
    category            VARCHAR(100),
    subcategory         VARCHAR(100),
    brand               VARCHAR(100),
    price               NUMERIC(12,2),
    discount            NUMERIC(5,2),
    final_price         NUMERIC(12,2),
    rating              NUMERIC(3,2),
    review_count        INTEGER,
    stock               INTEGER,
    seller_id           VARCHAR(50),
    seller_rating       NUMERIC(3,2),
    purchase_date       DATE,
    shipping_time_days  INTEGER,
    location            VARCHAR(100),
    device              VARCHAR(50),
    payment_method      VARCHAR(50),
    is_returned         BOOLEAN,
    delivery_status     VARCHAR(50)
);

-- ==========================================
-- KPI VENTAS MENSUALES (RF3)
-- ==========================================
CREATE TABLE IF NOT EXISTS analytics.kpi_ventas_mensuales (
    anio            INTEGER,
    mes             INTEGER,
    total_orders    INTEGER,
    revenue         NUMERIC(14,2),
    avg_ticket      NUMERIC(14,2)
);

-- ==========================================
-- KPI VENTAS POR DISPOSITIVO (RF3, RF5)
-- ==========================================
CREATE TABLE IF NOT EXISTS analytics.kpi_ventas_dispositivo (
    device          VARCHAR(50),
    category        VARCHAR(100),
    total_orders    INTEGER,
    revenue         NUMERIC(14,2)
);

-- ==========================================
-- KPI EXPERIENCIA CLIENTE (RF5)
-- ==========================================
CREATE TABLE IF NOT EXISTS analytics.kpi_experiencia_cliente (
    category            VARCHAR(100),
    avg_rating          NUMERIC(4,2),
    return_rate         NUMERIC(6,2),
    avg_shipping_days   NUMERIC(6,2)
);

-- ==========================================
-- KPI SATISFACCION POR CIUDAD (RF5)
-- ==========================================
CREATE TABLE IF NOT EXISTS analytics.kpi_satisfaccion_ciudad (
    location        VARCHAR(100),
    avg_rating      NUMERIC(4,2),
    total_orders    INTEGER,
    return_rate     NUMERIC(6,2)
);

-- ==========================================
-- KPI VENDEDORES (RF6)
-- ==========================================
CREATE TABLE IF NOT EXISTS analytics.kpi_vendedores (
    seller_id       VARCHAR(50),
    total_orders    INTEGER,
    revenue         NUMERIC(14,2),
    avg_rating      NUMERIC(4,2),
    return_rate     NUMERIC(6,2)
);

-- ==========================================
-- KPI LOGISTICA POR CIUDAD (RF4)
-- ==========================================
CREATE TABLE IF NOT EXISTS analytics.kpi_logistica_ciudad (
    location            VARCHAR(100),
    avg_shipping_days   NUMERIC(6,2),
    return_rate         NUMERIC(6,2),
    total_orders        INTEGER
);

-- ==========================================
-- KPI DEMORAS MENSUALES (RF4)
-- ==========================================
CREATE TABLE IF NOT EXISTS analytics.kpi_demoras_mensuales (
    anio            INTEGER,
    mes             INTEGER,
    total_delayed   INTEGER,
    total_orders    INTEGER,
    pct_delayed     NUMERIC(6,2)
);