from pathlib import Path
import pandas as pd


EXPECTED_COLUMNS = [
    "user_id",
    "product_id",
    "category",
    "subcategory",
    "brand",
    "price",
    "discount",
    "final_price",
    "rating",
    "review_count",
    "stock",
    "seller_id",
    "seller_rating",
    "purchase_date",
    "shipping_time_days",
    "location",
    "device",
    "payment_method",
    "is_returned",
    "delivery_status"
]


def validate_csv():

    file_path = Path("/opt/airflow/data/input/amazon_ecommerce.csv")

    if not file_path.exists():
        raise FileNotFoundError(
            f"Archivo no encontrado: {file_path}"
        )

    df = pd.read_csv(file_path)

    missing_columns = [
        col for col in EXPECTED_COLUMNS
        if col not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Faltan columnas: {missing_columns}"
        )

    print("CSV validado correctamente")