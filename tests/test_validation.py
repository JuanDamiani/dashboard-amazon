"""
Pruebas minimas del pipeline.

Estas pruebas documentan parte de la cobertura de RF11 y RF14: validan que un
CSV correcto pase, que falten columnas obligatorias falle y que la carga tabular
prepare metadata antes de cargar staging. La deduplicacion queda en SQL.
"""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd

from scripts.config import COLUMNAS_REQUERIDAS
from scripts.load.load_staging import preparar_staging_tabular
from scripts.validation import validate_csv as validation


VALID_COLUMNS = [
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
    "delivery_status",
]


VALID_ROW = {
    "user_id": "U1",
    "product_id": "P1",
    "category": "Electronics",
    "subcategory": "Mobile",
    "brand": "Samsung",
    "price": "1000",
    "discount": "10",
    "final_price": "900",
    "rating": "4.5",
    "review_count": "20",
    "stock": "50",
    "seller_id": "S1",
    "seller_rating": "4.2",
    "purchase_date": "4/3/2025",
    "shipping_time_days": "3",
    "location": "Delhi",
    "device": "Web",
    "payment_method": "UPI",
    "is_returned": "False",
    "delivery_status": "Delivered",
}


def write_csv(path, rows, columns=VALID_COLUMNS):
    pd.DataFrame(rows, columns=columns).to_csv(path, sep=";", index=False)


def write_comma_csv(path, rows, columns=VALID_COLUMNS):
    pd.DataFrame(rows, columns=columns).to_csv(path, sep=",", index=False)


class CsvValidationTests(unittest.TestCase):
    def test_valid_csv_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            csv_path = Path(tmp) / "amazon.csv"
            write_csv(csv_path, [VALID_ROW])

            with patch.object(validation, "get_selected_csv_path", return_value=csv_path), patch.object(
                validation, "record_validation_summary"
            ):
                validation.validate_csv()

    def test_valid_comma_csv_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            csv_path = Path(tmp) / "amazon_comma.csv"
            write_comma_csv(csv_path, [VALID_ROW])

            with patch.object(validation, "get_selected_csv_path", return_value=csv_path), patch.object(
                validation, "record_validation_summary"
            ):
                validation.validate_csv()

    def test_missing_column_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            csv_path = Path(tmp) / "amazon.csv"
            columns = [col for col in VALID_COLUMNS if col != "seller_id"]
            row = {key: value for key, value in VALID_ROW.items() if key != "seller_id"}
            write_csv(csv_path, [row], columns=columns)

            with patch.object(validation, "get_selected_csv_path", return_value=csv_path), patch.object(
                validation, "record_validation_summary"
            ):
                with self.assertRaises(ValueError):
                    validation.validate_csv()

    def test_prepare_tabular_staging_keeps_payload_and_metadata(self):
        df = pd.DataFrame([VALID_ROW])
        result = preparar_staging_tabular(df, "amazon.csv", "batch-1")

        self.assertEqual(len(result), 1)
        self.assertEqual(result["source_file"].iloc[0], "amazon.csv")
        self.assertEqual(result["batch_id"].iloc[0], "batch-1")
        self.assertEqual(result["user_id"].iloc[0], "U1")
        self.assertEqual(list(result.columns), ["source_file", "batch_id"] + COLUMNAS_REQUERIDAS)


if __name__ == "__main__":
    unittest.main()
