from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine


def load_staging():

    file_path = Path("/opt/airflow/data/input/amazon_ecommerce.csv")

    df = pd.read_csv(file_path)

    # ==========================================
    # ELIMINAR DUPLICADOS
    # ==========================================

    rows_before = len(df)

    df.drop_duplicates(
        subset=[
            "user_id",
            "product_id",
            "purchase_date"
        ],
        inplace=True
    )

    rows_after = len(df)

    removed_duplicates = rows_before - rows_after

    print(f"Duplicados eliminados: {removed_duplicates}")

    # ==========================================
    # CONEXIÓN POSTGRES
    # ==========================================

    engine = create_engine(
        "postgresql+psycopg2://dwh:dwh123@postgres-dwh:5432/amazon_dwh"
    )

    # ==========================================
    # CARGA STAGING
    # ==========================================

    df.to_sql(
        "amazon_sales_raw",
        engine,
        schema="staging",
        if_exists="replace",
        index=False
    )

    print(f"{len(df)} filas cargadas")