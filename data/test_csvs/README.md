# CSVs de prueba

Estos archivos estan pensados para probar el flujo desde Streamlit:

- `01_valido_semicolon.csv`: CSV valido con separador `;`.
- `02_valido_comma.csv`: CSV valido con separador `,`.
- `03_columnas_faltantes.csv`: falla validacion porque no tiene `seller_id`.
- `04_valores_invalidos.csv`: falla validacion por `delivery_status`, `is_returned`, rating y descuento invalidos.
- `05_advertencias.csv`: valida con advertencias por categoria, metodo de pago y dispositivo nuevos.
- `06_historico_nuevo.csv`: CSV valido con fechas posteriores para probar acumulacion historica.
- `07_mismo_nombre_contenido_distinto.csv`: valido; sirve para comprobar que el control de duplicados depende de nombre + hash.

Para usarlos, entra a Streamlit, pestaña `Carga`, sube uno de estos archivos y ejecuta el pipeline.
