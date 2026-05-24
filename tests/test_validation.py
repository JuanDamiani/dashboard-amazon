"""
Pruebas minimas del pipeline.

Estas pruebas documentan parte de la cobertura de RF11 y RF14: validan que un
CSV correcto pase, que falten columnas obligatorias falle y que las claves
sale_id se mantengan estables y se dedupliquen antes de cargar la fact table.
"""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd

from scripts.transform.clean_staging import eliminar_duplicados_sale_id, generar_sale_id
from scripts.load.load_staging import convertir_a_jsonb, eliminar_duplicados
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

    def test_sale_id_is_stable_for_same_business_key(self):
        df = pd.DataFrame([VALID_ROW, {**VALID_ROW, "rating": "3.0"}])
        result = generar_sale_id(df)

        self.assertEqual(result["sale_id"].iloc[0], result["sale_id"].iloc[1])

    def test_sale_id_duplicates_are_removed_before_load(self):
        df = pd.DataFrame([VALID_ROW, {**VALID_ROW, "rating": "3.0"}])
        df = generar_sale_id(df)
        result = eliminar_duplicados_sale_id(df)

        self.assertEqual(len(result), 1)

    def test_convert_to_jsonb_keeps_payload_and_metadata(self):
        df = pd.DataFrame([VALID_ROW])
        result = convertir_a_jsonb(df, "amazon.csv", "batch-1")

        self.assertEqual(len(result), 1)
        self.assertEqual(result["source_file"].iloc[0], "amazon.csv")
        self.assertEqual(result["batch_id"].iloc[0], "batch-1")
        self.assertEqual(result["raw_payload"].iloc[0]["user_id"], "U1")

    def test_load_dedup_uses_seen_keys_across_chunks(self):
        seen_keys = set()
        first = pd.DataFrame([VALID_ROW])
        second = pd.DataFrame([{**VALID_ROW, "rating": "3.0"}])

        first_result = eliminar_duplicados(first, seen_keys=seen_keys)
        second_result = eliminar_duplicados(second, seen_keys=seen_keys)

        self.assertEqual(len(first_result), 1)
        self.assertEqual(len(second_result), 0)


if __name__ == "__main__":
    unittest.main()
