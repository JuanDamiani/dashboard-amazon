import os
from pathlib import Path

# Rutas
ARCHIVO_CSV = Path(os.getenv("RUTA_CSV", "/opt/airflow/data/input/amazon_ecommerce.csv"))

# Columnas
COLUMNAS_REQUERIDAS = [
    "user_id", "product_id", "category", "subcategory", "brand",
    "price", "discount", "final_price", "rating", "review_count",
    "stock", "seller_id", "seller_rating", "purchase_date",
    "shipping_time_days", "location", "device", "payment_method",
    "is_returned", "delivery_status"
]

COLUMNAS_CRITICAS = [
    "user_id", "product_id", "seller_id",
    "purchase_date", "final_price",
    "delivery_status", "is_returned"
]

COLUMNAS_NUMERICAS = [
    "price", "discount", "final_price",
    "rating", "review_count", "stock", "seller_rating", "shipping_time_days"
]

VALORES_ESTRICTOS = {
    "delivery_status": ["Delivered", "Delayed", "In Transit", "Returned"],
    "is_returned":     ["True", "False"]
}

VALORES_ADVERTENCIA = {
    "category":       ["Electronics", "Sports", "Beauty", "Home", "Clothing"],
    "payment_method": ["UPI", "Credit Card", "Debit Card", "Cash on Delivery"],
    "device":         ["Mobile App", "Web", "Tablet"]
}


# Conexion a PostgreSQL
DWH_DB_USER = os.getenv("DWH_DB_USER", "dwh")
DWH_DB_PASSWORD = os.getenv("DWH_DB_PASSWORD", "dwh123")
DWH_DB_HOST = os.getenv("DWH_DB_HOST", "postgres-dwh")
DWH_DB_PORT = os.getenv("DWH_DB_PORT", "5432")
DWH_DB_NAME = os.getenv("DWH_DB_NAME", "amazon_dwh")

DB_URL = os.getenv(
    "DB_URL",
    f"postgresql+psycopg2://{DWH_DB_USER}:{DWH_DB_PASSWORD}@{DWH_DB_HOST}:{DWH_DB_PORT}/{DWH_DB_NAME}"
)

CSV_SEPARATOR = ";"
