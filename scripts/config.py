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
    "rating", "stock", "seller_rating", "shipping_time_days"
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


# Conexión a PostgreSQL
DB_URL = "postgresql+psycopg2://dwh:dwh123@postgres-dwh:5432/amazon_dwh"