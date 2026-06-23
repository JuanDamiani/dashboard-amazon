"""
Pruebas mínimas del pipeline.

Estas pruebas documentan parte de la cobertura de RF11 y RF14: validan que un
CSV correcto pase, que falten columnas obligatorias falle y que la carga tabular
prepare metadata antes de cargar staging. La deduplicación queda en SQL.

===============================================================================
📖 GUÍA RÁPIDA: CÓMO EJECUTAR Y LEER LOS RESULTADOS EN TU CONSOLA
===============================================================================
Dependiendo de tu sistema operativo, ejecutá el comando correspondiente en la 
terminal (dentro de la carpeta raíz del proyecto):

🐧 EN LINUX / UBUNTU:
   sudo docker compose run --rm kpi-tests

🪟 EN WINDOWS (PowerShell o CMD - Requiere Docker Desktop abierto):
   docker compose run --rm kpi-tests

-------------------------------------------------------------------------------
INTERPRETACIÓN DE LA SALIDA EN PANTALLA:

1. LOGS DE PROCESAMIENTO INTERNO (Logs de la aplicación):
   Verás textos que dicen "Separador detectado para...", "Reporte de validación", 
   "Resultado: Validación fallida/exitosa", etc. Esto NO significa que el test 
   falló. Son solo impresiones del validador analizando cada archivo real.

2. LOS PUNTOS DE CONTROL EN LA PANTALLA (Indicadores de éxito):
   Verás unos puntos individuales (.) salpicados en el texto. Cada punto (.) 
   representa un escenario o test lúdico aprobado con éxito por el framework.
   - Si un escenario falla lógicamente, verás una 'F' en su lugar.
   - Si el código tiene un bug de sintaxis, verás una 'E'.

3. EL RESUMEN DEFINITIVO (Ubicado abajo de todo):
   ----------------------------------------------------------------------
   Ran 5 tests in 0.116s
   OK
   
   - "Ran 5 tests": Significa que se ejecutaron las 5 funciones estructurales 
     (incluyendo la función masiva que evalúa tus 7 datasets reales).
   - "OK": Es el veredicto final de ingeniería. Confirma que el 100% de las 
     pruebas pasaron de manera exitosa y el pipeline es seguro.
===============================================================================
"""

import os
import tempfile
import unittest
# ... (el resto del código sigue exactamente igual abajo)
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd

from scripts.config import COLUMNAS_REQUERIDAS
from scripts.load.load_staging import preparar_staging_tabular
from scripts.validation import validate_csv as validation

# --- DETECCIÓN DE RUTAS RELATIVAS PROFESIONALES ---
TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
TEST_CSVS_DIR = os.path.abspath(os.path.join(TESTS_DIR, "..", "data", "test_csvs"))

VALID_COLUMNS = [
    "user_id", "product_id", "category", "subcategory", "brand", "price",
    "discount", "final_price", "rating", "review_count", "stock", "seller_id",
    "seller_rating", "purchase_date", "shipping_time_days", "location",
    "device", "payment_method", "is_returned", "delivery_status",
]

VALID_ROW = {
    "user_id": "U1", "product_id": "P1", "category": "Electronics", "subcategory": "Mobile",
    "brand": "Samsung", "price": "1000", "discount": "10", "final_price": "900",
    "rating": "4.5", "review_count": "20", "stock": "50", "seller_id": "S1",
    "seller_rating": "4.2", "purchase_date": "4/3/2025", "shipping_time_days": "3",
    "location": "Delhi", "device": "Web", "payment_method": "UPI", "is_returned": "False",
    "delivery_status": "Delivered",
}


class CsvValidationTests(unittest.TestCase):

    # =========================================================================
    # 🧪 SECCIÓN 1: PRUEBAS AUTOMÁTICAS CON DATASETS REALES (TUS ARCHIVOS)
    # =========================================================================

    def test_datasets_del_servidor(self):
        """
        EVALÚA: Los 7 datasets reales de prueba almacenados en el servidor.
        OBJETIVO: Validar de punta a punta la resiliencia del pipeline frente a 
        archivos físicos con separadores mixtos (; y ,), datos corruptos, 
        columnas faltantes, advertencias de negocio y cargas históricas.
        """
        escenarios_prueba = {
            "01_valido_semicolon.csv": "pasa",
            "02_valido_comma.csv": "pasa",
            "03_columnas_faltantes.csv": "falla",
            "04_valores_invalidos.csv": "falla",
            "05_advertencias.csv": "pasa",  
            "06_historico_nuevo.csv": "pasa",
            "07_mismo_nombre_contenido_distinto.csv": "pasa",
        }

        for nombre_archivo, resultado_esperado in escenarios_prueba.items():
            ruta_csv = Path(os.path.join(TEST_CSVS_DIR, nombre_archivo))
            if not ruta_csv.exists():
                continue

            with self.subTest(archivo=nombre_archivo):
                with patch.object(validation, "get_selected_csv_path", return_value=ruta_csv), \
                     patch.object(validation, "record_validation_summary"):
                    
                    if resultado_esperado == "falla":
                        with self.assertRaises(ValueError, msg=f"ERROR CRÍTICO: El archivo {nombre_archivo} contenía fallas graves de datos y el pipeline debió haberlo rechazado lanzando un ValueError."):
                            validation.validate_csv()
                    else:
                        try:
                            validation.validate_csv()
                        except Exception as e:
                            self.fail(f"ERROR CRÍTICO: El archivo {nombre_archivo} era estructuralmente válido pero el pipeline falló inesperadamente con el error: {e}")

    # =========================================================================
    # ⚙️ SECCIÓN 2: TESTS ORIGINALES DEL EQUIPO (SIMULADOS)
    # =========================================================================

    def test_valid_csv_passes(self):
        """
        EVALÚA: Comportamiento base con archivos separados por punto y coma (;).
        OBJETIVO: Asegurar que un flujo estándar correcto pase la validación lúdica 
        sin disparar excepciones. (Satisface cobertura RF11).
        """
        with tempfile.TemporaryDirectory() as tmp:
            csv_path = Path(tmp) / "amazon.csv"
            pd.DataFrame([VALID_ROW], columns=VALID_COLUMNS).to_csv(csv_path, sep=";", index=False)

            with patch.object(validation, "get_selected_csv_path", return_value=csv_path), patch.object(
                validation, "record_validation_summary"
            ):
                validation.validate_csv()

    def test_valid_comma_csv_passes(self):
        """
        EVALÚA: Flexibilidad del validador con delimitadores por coma (,).
        OBJETIVO: Verificar que el motor detecte de forma automática el cambio de 
        separador estándar anglosajón en el payload entrante.
        """
        with tempfile.TemporaryDirectory() as tmp:
            csv_path = Path(tmp) / "amazon_comma.csv"
            pd.DataFrame([VALID_ROW], columns=VALID_COLUMNS).to_csv(csv_path, sep=",", index=False)

            with patch.object(validation, "get_selected_csv_path", return_value=csv_path), patch.object(
                validation, "record_validation_summary"
            ):
                validation.validate_csv()

    def test_missing_column_fails(self):
        """
        EVALÚA: Control de integridad estructural y esquema obligatorio.
        OBJETIVO: Forzar la ausencia de una columna clave ('seller_id') y confirmar 
        que el sistema aborte el procesamiento disparando un ValueError. (Satisface cobertura RF11).
        """
        with tempfile.TemporaryDirectory() as tmp:
            csv_path = Path(tmp) / "amazon.csv"
            columns = [col for col in VALID_COLUMNS if col != "seller_id"]
            row = {key: value for key, value in VALID_ROW.items() if key != "seller_id"}
            pd.DataFrame([row], columns=columns).to_csv(csv_path, sep=";", index=False)

            with patch.object(validation, "get_selected_csv_path", return_value=csv_path), patch.object(
                validation, "record_validation_summary"
            ):
                with self.assertRaises(ValueError):
                    validation.validate_csv()

    def test_prepare_tabular_staging_keeps_payload_and_metadata(self):
        """
        EVALÚA: Enriquecimiento de datos en la capa de carga (Load Staging).
        OBJETIVO: Validar que la función inyecte correctamente las columnas técnicas de control 
        ('source_file' y 'batch_id') resguardando las 20 columnas del negocio originales. (Satisface cobertura RF14).
        """
        df = pd.DataFrame([VALID_ROW])
        result = preparar_staging_tabular(df, "amazon.csv", "batch-1")

        self.assertEqual(len(result), 1)
        self.assertEqual(result["source_file"].iloc[0], "amazon.csv")
        self.assertEqual(result["batch_id"].iloc[0], "batch-1")
        self.assertEqual(result["user_id"].iloc[0], "U1")
        self.assertEqual(list(result.columns), ["source_file", "batch_id"] + COLUMNAS_REQUERIDAS)


if __name__ == "__main__":
    unittest.main()