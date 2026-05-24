#!/usr/bin/env python3
"""
Provisiona Metabase para que el proyecto quede listo despues de clonar el repo.

Este script cubre la parte de BI del SRS:
- RF1 a RF6: crea dashboards y preguntas SQL para resumen, ventas, logistica,
  clientes y vendedores.
- RF2: agrega filtros globales y los conecta a las preguntas.
- RF7: deja preguntas exportables desde Metabase.
- RF8: organiza la navegacion en dashboards dentro de una coleccion.

Es idempotente: si Metabase ya esta configurado, actualiza los recursos por
nombre en lugar de crear duplicados.
"""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request
from typing import Any


BASE = os.getenv("METABASE_URL", "http://metabase:3000").rstrip("/")

ADMIN_EMAIL = os.getenv("METABASE_ADMIN_EMAIL", "admin@local.test")
ADMIN_PASSWORD = os.getenv("METABASE_ADMIN_PASSWORD", "AdminLocal2026!")
ADMIN_FIRST = os.getenv("METABASE_ADMIN_FIRST_NAME", "Admin")
ADMIN_LAST = os.getenv("METABASE_ADMIN_LAST_NAME", "Local")
SITE_NAME = os.getenv("METABASE_SITE_NAME", "Amazon E-Commerce Dashboard")

DWH_NAME = os.getenv("METABASE_DWH_NAME", "Amazon DWH")
DWH_HOST = os.getenv("DWH_DB_HOST", "postgres-dwh")
DWH_PORT = int(os.getenv("DWH_DB_PORT", "5432"))
DWH_DB = os.getenv("DWH_DB_NAME", "amazon_dwh")
DWH_USER = os.getenv("DWH_DB_USER", "dwh")
DWH_PASSWORD = os.getenv("DWH_DB_PASSWORD", "dwh123")

COLLECTION_NAME = os.getenv("METABASE_COLLECTION_NAME", "Amazon E-Commerce")


def request_json(
    method: str,
    path: str,
    payload: dict[str, Any] | None = None,
    session_id: str | None = None,
    timeout: int = 120,
) -> tuple[int, Any]:
    """Ejecuta una llamada JSON contra la API de Metabase."""
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    headers = {"Accept": "application/json"}
    if data is not None:
        headers["Content-Type"] = "application/json"
    if session_id:
        headers["X-Metabase-Session"] = session_id

    req = urllib.request.Request(f"{BASE}{path}", data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            body = response.read().decode("utf-8", errors="replace")
            if not body.strip():
                return response.status, {}
            try:
                return response.status, json.loads(body)
            except json.JSONDecodeError:
                return response.status, body
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        try:
            parsed = json.loads(body)
        except json.JSONDecodeError:
            parsed = body
        raise RuntimeError(f"{method} {path} fallo con HTTP {exc.code}: {parsed}") from exc


def wait_metabase(max_wait_s: int = 300) -> None:
    """Espera a que Metabase responda antes de intentar configurarlo."""
    deadline = time.time() + max_wait_s
    while time.time() < deadline:
        try:
            status, _ = request_json("GET", "/api/health", timeout=10)
            if status == 200:
                return
        except Exception:
            pass
        time.sleep(3)
    raise RuntimeError("Metabase no respondio a /api/health a tiempo.")


def setup_admin_if_needed() -> None:
    """Completa el asistente inicial si Metabase todavia tiene setup-token."""
    status, props = request_json("GET", "/api/session/properties")
    if status != 200 or not isinstance(props, dict):
        raise RuntimeError("Respuesta inesperada de /api/session/properties.")

    token = props.get("setup-token") or props.get("setup_token")
    if not token:
        print("Metabase ya estaba inicializado.")
        return

    payload = {
        "token": token,
        "user": {
            "first_name": ADMIN_FIRST,
            "last_name": ADMIN_LAST,
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD,
        },
        "prefs": {
            "site_name": SITE_NAME,
            "site_locale": "es",
            "allow_tracking": False,
        },
    }
    try:
        request_json("POST", "/api/setup", payload)
    except RuntimeError as exc:
        # Algunas instancias conservan setup-token en properties aunque ya
        # exista el primer usuario. En ese caso Metabase responde 403 y el
        # flujo debe continuar con login para actualizar dashboards.
        if "HTTP 403" in str(exc) and "/api/setup" in str(exc):
            print("Metabase ya tenia usuario inicial; se continua con login.")
            return
        raise
    print(f"Metabase inicializado con usuario admin {ADMIN_EMAIL}.")


def login() -> str:
    """Obtiene una sesion para crear bases, colecciones y dashboards."""
    _, response = request_json(
        "POST",
        "/api/session",
        {"username": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
    )
    if not isinstance(response, dict) or "id" not in response:
        raise RuntimeError("No se pudo iniciar sesion en Metabase.")
    return str(response["id"])


def find_by_name(items: list[dict[str, Any]], name: str) -> dict[str, Any] | None:
    """Busca un recurso activo por nombre."""
    for item in items:
        if item.get("name") == name and not item.get("archived", False):
            return item
    return None


def ensure_database(session_id: str) -> int:
    """Crea o reutiliza la conexion de Metabase al data warehouse."""
    _, response = request_json("GET", "/api/database", session_id=session_id)
    databases = response.get("data", []) if isinstance(response, dict) else []
    existing = find_by_name(databases, DWH_NAME)
    if existing:
        print(f"Base Metabase existente: {DWH_NAME} (id={existing['id']}).")
        return int(existing["id"])

    payload = {
        "name": DWH_NAME,
        "engine": "postgres",
        "details": {
            "host": DWH_HOST,
            "port": DWH_PORT,
            "dbname": DWH_DB,
            "user": DWH_USER,
            "password": DWH_PASSWORD,
            "ssl": False,
            "schema-filters-type": "inclusion",
            "schema-filters-patterns": "analytics,staging",
        },
        "is_full_sync": True,
        "is_on_demand": False,
        "schedules": {},
    }
    _, created = request_json("POST", "/api/database", payload, session_id=session_id)
    print(f"Base Metabase creada: {DWH_NAME} (id={created['id']}).")
    return int(created["id"])


def ensure_collection(session_id: str) -> int:
    """Crea o reutiliza la coleccion donde viven preguntas y dashboards."""
    _, collections = request_json("GET", "/api/collection", session_id=session_id)
    existing = find_by_name(collections if isinstance(collections, list) else [], COLLECTION_NAME)
    if existing:
        print(f"Coleccion existente: {COLLECTION_NAME} (id={existing['id']}).")
        return int(existing["id"])

    payload = {
        "name": COLLECTION_NAME,
        "description": "Coleccion de dashboards y preguntas del SRS Amazon e-commerce.",
        "color": "#509EE3",
    }
    _, created = request_json("POST", "/api/collection", payload, session_id=session_id)
    print(f"Coleccion creada: {COLLECTION_NAME} (id={created['id']}).")
    return int(created["id"])


def wait_for_fact_fields(session_id: str, database_id: int) -> dict[str, int]:
    """Sincroniza metadata y obtiene IDs de campos para mapear filtros."""
    try:
        request_json("POST", f"/api/database/{database_id}/sync_schema", session_id=session_id)
    except Exception as exc:
        print(f"Aviso: no se pudo disparar sync_schema: {exc}")

    required = ["purchase_date", "category", "location", "device", "payment_method"]
    deadline = time.time() + 180
    while time.time() < deadline:
        _, metadata = request_json("GET", f"/api/database/{database_id}/metadata", session_id=session_id)
        tables = metadata.get("tables", []) if isinstance(metadata, dict) else []
        fact_table = next(
            (table for table in tables if table.get("schema") == "analytics" and table.get("name") == "fact_orders"),
            None,
        )
        if fact_table:
            fields = {
                field["name"]: int(field["id"])
                for field in fact_table.get("fields", [])
                if field.get("name") in required
            }
            if all(name in fields for name in required):
                return fields
        time.sleep(5)
    raise RuntimeError("No se encontraron los campos de analytics.fact_orders para filtros.")


def filter_sql() -> str:
    """Bloque de filtros opcionales compartido por las preguntas SQL."""
    return (
        "WHERE 1 = 1\n"
        "[[AND {{purchase_date}}]]\n"
        "[[AND {{category}}]]\n"
        "[[AND {{location}}]]\n"
        "[[AND {{device}}]]\n"
        "[[AND {{payment_method}}]]"
    )


def template_tags(field_ids: dict[str, int]) -> dict[str, dict[str, Any]]:
    """Define las variables Field Filter que Metabase conecta al dashboard."""
    return {
        "purchase_date": {
            "id": "purchase_date",
            "name": "purchase_date",
            "display-name": "Fecha de compra",
            "type": "dimension",
            "dimension": ["field", field_ids["purchase_date"], None],
            "widget-type": "date/all-options",
        },
        "category": {
            "id": "category",
            "name": "category",
            "display-name": "Categoria",
            "type": "dimension",
            "dimension": ["field", field_ids["category"], None],
            "widget-type": "category",
        },
        "location": {
            "id": "location",
            "name": "location",
            "display-name": "Ciudad",
            "type": "dimension",
            "dimension": ["field", field_ids["location"], None],
            "widget-type": "category",
        },
        "device": {
            "id": "device",
            "name": "device",
            "display-name": "Dispositivo",
            "type": "dimension",
            "dimension": ["field", field_ids["device"], None],
            "widget-type": "category",
        },
        "payment_method": {
            "id": "payment_method",
            "name": "payment_method",
            "display-name": "Metodo de pago",
            "type": "dimension",
            "dimension": ["field", field_ids["payment_method"], None],
            "widget-type": "category",
        },
    }


def dashboard_specs() -> list[dict[str, Any]]:
    """Declara dashboards y preguntas que materializan RF1 a RF8."""
    filters = filter_sql()
    return [
        {
            "name": "Resumen",
            "description": "RF1: resumen ejecutivo con KPIs principales, variacion mensual, categorias, entregas y pagos.",
            "cards": [
                {
                    "name": "KPI General",
                    "display": "table",
                    "query": f"""
SELECT COUNT(*) AS total_orders,
       ROUND(SUM(final_price)::numeric, 2) AS total_revenue,
       ROUND(AVG(final_price)::numeric, 2) AS avg_ticket,
       ROUND(AVG(rating)::numeric, 2) AS avg_product_rating,
       ROUND(AVG(seller_rating)::numeric, 2) AS avg_seller_rating,
       ROUND(AVG(shipping_time_days)::numeric, 2) AS avg_shipping_days,
       ROUND(AVG(CASE WHEN is_returned THEN 1.0 ELSE 0.0 END)::numeric * 100, 2) AS return_rate
FROM analytics.fact_orders
{filters}
""",
                },
                {
                    "name": "Variacion Mensual Reciente",
                    "display": "bar",
                    "query": f"""
WITH monthly AS (
    SELECT DATE_TRUNC('month', purchase_date)::date AS period_month,
           COUNT(*) AS total_orders,
           SUM(final_price) AS total_revenue,
           AVG(final_price) AS avg_ticket
    FROM analytics.fact_orders
    {filters}
    GROUP BY 1
),
variation AS (
    SELECT period_month,
           total_orders,
           ROUND(((total_orders - LAG(total_orders) OVER (ORDER BY period_month))::numeric / NULLIF(LAG(total_orders) OVER (ORDER BY period_month), 0)) * 100, 2) AS total_orders_variation_pct,
           ROUND(total_revenue::numeric, 2) AS total_revenue,
           ROUND(((total_revenue - LAG(total_revenue) OVER (ORDER BY period_month))::numeric / NULLIF(LAG(total_revenue) OVER (ORDER BY period_month), 0)) * 100, 2) AS total_revenue_variation_pct,
           ROUND(avg_ticket::numeric, 2) AS avg_ticket,
           ROUND(((avg_ticket - LAG(avg_ticket) OVER (ORDER BY period_month))::numeric / NULLIF(LAG(avg_ticket) OVER (ORDER BY period_month), 0)) * 100, 2) AS avg_ticket_variation_pct
    FROM monthly
)
SELECT * FROM variation
ORDER BY period_month DESC
LIMIT 12
""",
                },
                {
                    "name": "Ingresos Por Categoria",
                    "display": "bar",
                    "query": f"""
SELECT category,
       COUNT(*) AS total_orders,
       ROUND(SUM(final_price)::numeric, 2) AS total_revenue,
       ROUND(AVG(final_price)::numeric, 2) AS avg_ticket,
       ROUND(AVG(rating)::numeric, 2) AS avg_rating,
       ROUND(AVG(discount)::numeric, 2) AS avg_discount
FROM analytics.fact_orders
{filters}
GROUP BY category
ORDER BY total_revenue DESC
""",
                },
                {
                    "name": "Estado De Entregas",
                    "display": "bar",
                    "query": f"""
SELECT delivery_status,
       COUNT(*) AS total_orders,
       ROUND(AVG(shipping_time_days)::numeric, 2) AS avg_shipping_days,
       ROUND(AVG(CASE WHEN is_returned THEN 1.0 ELSE 0.0 END)::numeric * 100, 2) AS return_rate
FROM analytics.fact_orders
{filters}
GROUP BY delivery_status
ORDER BY total_orders DESC
""",
                },
                {
                    "name": "Metodo De Pago",
                    "display": "bar",
                    "query": f"""
SELECT payment_method,
       COUNT(*) AS total_orders,
       ROUND(SUM(final_price)::numeric, 2) AS total_revenue,
       ROUND(AVG(final_price)::numeric, 2) AS avg_ticket
FROM analytics.fact_orders
{filters}
GROUP BY payment_method
ORDER BY total_revenue DESC
""",
                },
            ],
        },
        {
            "name": "Ventas",
            "description": "RF3: evolucion de ventas, categorias, marcas, dispositivos y descuentos.",
            "cards": [
                {
                    "name": "Evolucion Mensual De Ventas",
                    "display": "line",
                    "query": f"""
SELECT DATE_TRUNC('month', purchase_date)::date AS period_month,
       COUNT(*) AS total_orders,
       ROUND(SUM(final_price)::numeric, 2) AS revenue,
       ROUND(AVG(final_price)::numeric, 2) AS avg_ticket
FROM analytics.fact_orders
{filters}
GROUP BY 1
ORDER BY period_month
""",
                },
                {
                    "name": "Ventas Por Marca",
                    "display": "bar",
                    "query": f"""
SELECT brand,
       COUNT(*) AS total_orders,
       ROUND(SUM(final_price)::numeric, 2) AS total_revenue,
       ROUND(AVG(final_price)::numeric, 2) AS avg_ticket,
       ROUND(AVG(rating)::numeric, 2) AS avg_rating,
       ROUND(AVG(seller_rating)::numeric, 2) AS avg_seller_rating
FROM analytics.fact_orders
{filters}
GROUP BY brand
ORDER BY total_revenue DESC
LIMIT 25
""",
                },
                {
                    "name": "Ventas Por Dispositivo Y Categoria",
                    "display": "table",
                    "query": f"""
SELECT device,
       category,
       COUNT(*) AS total_orders,
       ROUND(SUM(final_price)::numeric, 2) AS revenue,
       ROUND(AVG(final_price)::numeric, 2) AS avg_ticket
FROM analytics.fact_orders
{filters}
GROUP BY device, category
ORDER BY device, revenue DESC
""",
                },
                {
                    "name": "Descuento Vs Ordenes",
                    "display": "bar",
                    "query": f"""
SELECT CASE
           WHEN discount < 10 THEN '00-09%'
           WHEN discount < 20 THEN '10-19%'
           WHEN discount < 30 THEN '20-29%'
           WHEN discount < 40 THEN '30-39%'
           WHEN discount < 50 THEN '40-49%'
           WHEN discount < 60 THEN '50-59%'
           WHEN discount < 70 THEN '60-69%'
           WHEN discount < 80 THEN '70-79%'
           WHEN discount < 90 THEN '80-89%'
           ELSE '90-100%'
       END AS discount_range,
       COUNT(*) AS total_orders,
       ROUND(SUM(final_price)::numeric, 2) AS total_revenue,
       ROUND(AVG(final_price)::numeric, 2) AS avg_ticket
FROM analytics.fact_orders
{filters}
GROUP BY discount_range
ORDER BY discount_range
""",
                },
            ],
        },
        {
            "name": "Logistica",
            "description": "RF4: estados de entrega, ciudades, demoras y devoluciones.",
            "cards": [
                {
                    "name": "Tiempo Promedio Por Ciudad",
                    "display": "bar",
                    "query": f"""
SELECT location,
       COUNT(*) AS total_orders,
       ROUND(AVG(shipping_time_days)::numeric, 2) AS avg_shipping_days,
       ROUND(AVG(CASE WHEN is_returned THEN 1.0 ELSE 0.0 END)::numeric * 100, 2) AS return_rate
FROM analytics.fact_orders
{filters}
GROUP BY location
ORDER BY avg_shipping_days DESC
""",
                },
                {
                    "name": "Demoras Mensuales",
                    "display": "line",
                    "query": f"""
SELECT DATE_TRUNC('month', purchase_date)::date AS period_month,
       SUM(CASE WHEN delivery_status = 'Delayed' THEN 1 ELSE 0 END) AS delayed_orders,
       COUNT(*) AS total_orders,
       ROUND(AVG(CASE WHEN delivery_status = 'Delayed' THEN 1.0 ELSE 0.0 END)::numeric * 100, 2) AS delayed_rate
FROM analytics.fact_orders
{filters}
GROUP BY 1
ORDER BY period_month
""",
                },
                {
                    "name": "Devoluciones Por Categoria",
                    "display": "bar",
                    "query": f"""
SELECT category,
       SUM(CASE WHEN is_returned THEN 1 ELSE 0 END) AS returned_orders,
       COUNT(*) AS total_orders,
       ROUND(AVG(CASE WHEN is_returned THEN 1.0 ELSE 0.0 END)::numeric * 100, 2) AS return_rate
FROM analytics.fact_orders
{filters}
GROUP BY category
ORDER BY return_rate DESC
""",
                },
                {
                    "name": "Demora Vs Devolucion",
                    "display": "bar",
                    "visualization_settings": {
                        "graph.dimensions": ["shipping_time_days"],
                        "graph.metrics": ["total_orders", "returned_orders", "return_rate"],
                    },
                    "query": f"""
SELECT shipping_time_days,
       COUNT(*) AS total_orders,
       SUM(CASE WHEN is_returned THEN 1 ELSE 0 END) AS returned_orders,
       ROUND(AVG(CASE WHEN is_returned THEN 1.0 ELSE 0.0 END)::numeric * 100, 2) AS return_rate
FROM analytics.fact_orders
{filters}
GROUP BY shipping_time_days
ORDER BY shipping_time_days
""",
                },
            ],
        },
        {
            "name": "Clientes",
            "description": "RF5: satisfaccion, rating, devoluciones y comportamiento del cliente.",
            "cards": [
                {
                    "name": "Rating Por Categoria",
                    "display": "bar",
                    "query": f"""
SELECT category,
       ROUND(AVG(rating)::numeric, 2) AS avg_rating,
       ROUND(AVG(CASE WHEN is_returned THEN 1.0 ELSE 0.0 END)::numeric * 100, 2) AS return_rate,
       ROUND(AVG(shipping_time_days)::numeric, 2) AS avg_shipping_days,
       COUNT(*) AS total_orders
FROM analytics.fact_orders
{filters}
GROUP BY category
ORDER BY avg_rating DESC
""",
                },
                {
                    "name": "Satisfaccion Por Ciudad",
                    "display": "bar",
                    "query": f"""
SELECT location,
       ROUND(AVG(rating)::numeric, 2) AS avg_rating,
       COUNT(*) AS total_orders,
       ROUND(AVG(CASE WHEN is_returned THEN 1.0 ELSE 0.0 END)::numeric * 100, 2) AS return_rate
FROM analytics.fact_orders
{filters}
GROUP BY location
ORDER BY avg_rating DESC
""",
                },
                {
                    "name": "Distribucion De Ratings",
                    "display": "bar",
                    "visualization_settings": {
                        "graph.dimensions": ["rating"],
                        "graph.metrics": ["total_orders", "order_share_pct"],
                    },
                    "query": f"""
SELECT rating,
       COUNT(*) AS total_orders,
       ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) AS order_share_pct
FROM analytics.fact_orders
{filters}
GROUP BY rating
ORDER BY rating
""",
                },
                {
                    "name": "Metodo De Pago Vs Devolucion",
                    "display": "bar",
                    "query": f"""
SELECT payment_method,
       COUNT(*) AS total_orders,
       SUM(CASE WHEN is_returned THEN 1 ELSE 0 END) AS returned_orders,
       ROUND(AVG(CASE WHEN is_returned THEN 1.0 ELSE 0.0 END)::numeric * 100, 2) AS return_rate
FROM analytics.fact_orders
{filters}
GROUP BY payment_method
ORDER BY return_rate DESC
""",
                },
            ],
        },
        {
            "name": "Vendedores",
            "description": "RF6: ranking y control de performance de vendedores.",
            "cards": [
                {
                    "name": "Ranking De Vendedores",
                    "display": "table",
                    "query": f"""
SELECT seller_id,
       COUNT(*) AS total_orders,
       ROUND(SUM(final_price)::numeric, 2) AS total_revenue,
       ROUND(AVG(final_price)::numeric, 2) AS avg_ticket,
       ROUND(AVG(seller_rating)::numeric, 2) AS avg_seller_rating,
       ROUND(AVG(CASE WHEN is_returned THEN 1.0 ELSE 0.0 END)::numeric * 100, 2) AS return_rate
FROM analytics.fact_orders
{filters}
GROUP BY seller_id
ORDER BY total_revenue DESC
LIMIT 100
""",
                },
                {
                    "name": "Vendedores Con Mayor Tasa De Devolucion",
                    "display": "table",
                    "query": f"""
SELECT seller_id,
       COUNT(*) AS total_orders,
       ROUND(SUM(final_price)::numeric, 2) AS total_revenue,
       ROUND(AVG(seller_rating)::numeric, 2) AS avg_seller_rating,
       ROUND(AVG(CASE WHEN is_returned THEN 1.0 ELSE 0.0 END)::numeric * 100, 2) AS return_rate
FROM analytics.fact_orders
{filters}
GROUP BY seller_id
HAVING COUNT(*) >= 10
ORDER BY return_rate DESC, total_orders DESC
LIMIT 100
""",
                },
                {
                    "name": "Rating De Vendedor Vs Ingresos",
                    "display": "table",
                    "query": f"""
SELECT seller_id,
       COUNT(*) AS total_orders,
       ROUND(SUM(final_price)::numeric, 2) AS total_revenue,
       ROUND(AVG(seller_rating)::numeric, 2) AS avg_seller_rating,
       ROUND(AVG(CASE WHEN is_returned THEN 1.0 ELSE 0.0 END)::numeric * 100, 2) AS return_rate
FROM analytics.fact_orders
{filters}
GROUP BY seller_id
HAVING COUNT(*) >= 10
ORDER BY total_revenue DESC
""",
                },
            ],
        },
    ]


def ensure_card(
    session_id: str,
    database_id: int,
    collection_id: int,
    card_spec: dict[str, Any],
    tags: dict[str, dict[str, Any]],
    existing_cards: dict[str, dict[str, Any]],
) -> int:
    """Crea o actualiza una pregunta SQL por nombre."""
    payload = {
        "name": card_spec["name"],
        "description": "Pregunta SQL con filtros globales conectados al dashboard. Cubre requisitos del SRS.",
        "collection_id": collection_id,
        "display": card_spec["display"],
        "dataset_query": {
            "database": database_id,
            "type": "native",
            "native": {
                "query": card_spec["query"].strip(),
                "template-tags": tags,
            },
        },
        "visualization_settings": card_spec.get("visualization_settings", {}),
    }

    existing = existing_cards.get(card_spec["name"])
    if existing:
        request_json("PUT", f"/api/card/{existing['id']}", payload, session_id=session_id)
        return int(existing["id"])

    _, created = request_json("POST", "/api/card", payload, session_id=session_id)
    return int(created["id"])


def ensure_dashboard(
    session_id: str,
    collection_id: int,
    dash_spec: dict[str, Any],
    card_ids: list[int],
    existing_dashboards: dict[str, dict[str, Any]],
) -> int:
    """Crea o actualiza un dashboard y su layout de tarjetas."""
    existing = existing_dashboards.get(dash_spec["name"])
    payload = {
        "name": dash_spec["name"],
        "description": dash_spec["description"],
        "collection_id": collection_id,
    }

    if existing:
        dashboard_id = int(existing["id"])
        request_json("PUT", f"/api/dashboard/{dashboard_id}", payload, session_id=session_id)
    else:
        _, created = request_json("POST", "/api/dashboard", payload, session_id=session_id)
        dashboard_id = int(created["id"])

    parameters = [
        {"id": "purchase_date", "name": "Fecha de compra", "slug": "purchase_date", "type": "date/all-options", "sectionId": "date"},
        {"id": "category", "name": "Categoria", "slug": "category", "type": "category", "sectionId": "string"},
        {"id": "location", "name": "Ciudad", "slug": "location", "type": "category", "sectionId": "string"},
        {"id": "device", "name": "Dispositivo", "slug": "device", "type": "category", "sectionId": "string"},
        {"id": "payment_method", "name": "Metodo de pago", "slug": "payment_method", "type": "category", "sectionId": "string"},
    ]

    dashcards = []
    for idx, card_id in enumerate(card_ids):
        dashcards.append(
            {
                "id": -(idx + 1),
                "card_id": card_id,
                "row": (idx // 2) * 5,
                "col": (idx % 2) * 12,
                "size_x": 12,
                "size_y": 5,
                "visualization_settings": {},
                "parameter_mappings": [
                    {"parameter_id": param["id"], "card_id": card_id, "target": ["dimension", ["template-tag", param["id"]]]}
                    for param in parameters
                ],
            }
        )

    request_json(
        "PUT",
        f"/api/dashboard/{dashboard_id}",
        {"parameters": parameters, "dashcards": dashcards},
        session_id=session_id,
    )
    return dashboard_id


def list_cards(session_id: str) -> dict[str, dict[str, Any]]:
    """Devuelve preguntas activas indexadas por nombre."""
    _, response = request_json("GET", "/api/card", session_id=session_id)
    cards = response if isinstance(response, list) else response.get("data", [])
    return {card["name"]: card for card in cards if not card.get("archived", False)}


def list_dashboards(session_id: str) -> dict[str, dict[str, Any]]:
    """Devuelve dashboards activos por nombre y archiva duplicados del setup."""
    _, response = request_json("GET", "/api/dashboard", session_id=session_id)
    dashboards = response.get("data", []) if isinstance(response, dict) else response
    target_names = {dash["name"] for dash in dashboard_specs()}
    grouped: dict[str, list[dict[str, Any]]] = {name: [] for name in target_names}

    for dash in dashboards if isinstance(dashboards, list) else []:
        if dash.get("name") in target_names and not dash.get("archived", False):
            grouped[dash["name"]].append(dash)

    selected: dict[str, dict[str, Any]] = {}
    for name, items in grouped.items():
        items.sort(key=lambda item: int(item["id"]))
        if not items:
            continue
        selected[name] = items[0]
        for duplicate in items[1:]:
            request_json(
                "PUT",
                f"/api/dashboard/{duplicate['id']}",
                {"archived": True},
                session_id=session_id,
            )
            print(f"Dashboard duplicado archivado: {name} (id={duplicate['id']}).")

    return selected


def main() -> None:
    wait_metabase()
    setup_admin_if_needed()
    session_id = login()
    database_id = ensure_database(session_id)
    collection_id = ensure_collection(session_id)
    field_ids = wait_for_fact_fields(session_id, database_id)
    tags = template_tags(field_ids)

    existing_cards = list_cards(session_id)
    existing_dashboards = list_dashboards(session_id)

    for dash in dashboard_specs():
        card_ids = [
            ensure_card(session_id, database_id, collection_id, card, tags, existing_cards)
            for card in dash["cards"]
        ]
        dashboard_id = ensure_dashboard(session_id, collection_id, dash, card_ids, existing_dashboards)
        print(f"Dashboard listo: {dash['name']} (id={dashboard_id}, tarjetas={len(card_ids)}).")

    print("Metabase quedo provisionado correctamente.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR metabase_auto_setup: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
