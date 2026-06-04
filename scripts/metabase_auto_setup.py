#!/usr/bin/env python3
"""
Provisiona Metabase con un unico dashboard con tabs.

Dashboard: Amazon E-Commerce Analytics
Tabs: Resumen, Ventas, Logistica, Clientes, Vendedores, Glosario

Paleta Amazon:
- Naranja principal: #FF9900
- Azul principal:   #146EB4
- Oscuro:           #232F3E
- Naranja claro:    #FEBD69
- Gris neutro:      #687078
- Verde exito:      #067D62
- Rojo alerta:      #D13212

Cubre RF1 a RF9 del SRS.
"""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request
from typing import Any


BASE              = os.getenv("METABASE_URL", "http://metabase:3000").rstrip("/")
ADMIN_EMAIL       = os.getenv("METABASE_ADMIN_EMAIL", "admin@local.test")
ADMIN_PASSWORD    = os.getenv("METABASE_ADMIN_PASSWORD", "AdminLocal2026!")
ADMIN_FIRST       = os.getenv("METABASE_ADMIN_FIRST_NAME", "Admin")
ADMIN_LAST        = os.getenv("METABASE_ADMIN_LAST_NAME", "Local")
SITE_NAME         = os.getenv("METABASE_SITE_NAME", "Amazon E-Commerce Dashboard")
DWH_NAME          = os.getenv("METABASE_DWH_NAME", "Amazon DWH")
DWH_HOST          = os.getenv("DWH_DB_HOST", "postgres-dwh")
DWH_PORT          = int(os.getenv("DWH_DB_PORT", "5432"))
DWH_DB            = os.getenv("DWH_DB_NAME", "amazon_dwh")
DWH_USER          = os.getenv("DWH_DB_USER", "dwh")
DWH_PASSWORD      = os.getenv("DWH_DB_PASSWORD", "dwh123")
COLLECTION_NAME   = os.getenv("METABASE_COLLECTION_NAME", "Amazon E-Commerce")
DASHBOARD_NAME    = "Amazon E-Commerce Analytics"

# Paleta Amazon
C_ORANGE  = "#FF9900"
C_BLUE    = "#146EB4"
C_DARK    = "#232F3E"
C_LIGHT   = "#FEBD69"
C_GRAY    = "#687078"
C_GREEN   = "#067D62"
C_RED     = "#D13212"
C_BLUE2   = "#4A90D9"
C_ORANGE2 = "#F0A030"

PALETTE = [C_ORANGE, C_BLUE, C_GREEN, C_RED, C_LIGHT, C_GRAY, C_DARK, C_BLUE2]

# Grilla de 24 columnas
COL_FULL    = 24
COL_HALF    = 12
COL_THIRD   = 8
COL_QUARTER = 6
COL_SIXTH   = 4
H_KPI       = 3
H_CHART     = 6
H_CHART_L   = 8
H_TABLE     = 7


# =========================================================
# HTTP
# =========================================================

def request_json(method, path, payload=None, session_id=None, timeout=120):
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    headers = {"Accept": "application/json"}
    if data is not None:
        headers["Content-Type"] = "application/json"
    if session_id:
        headers["X-Metabase-Session"] = session_id
    req = urllib.request.Request(f"{BASE}{path}", data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            if not body.strip():
                return resp.status, {}
            try:
                return resp.status, json.loads(body)
            except json.JSONDecodeError:
                return resp.status, body
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        try:
            parsed = json.loads(body)
        except json.JSONDecodeError:
            parsed = body
        raise RuntimeError(f"{method} {path} fallo con HTTP {exc.code}: {parsed}") from exc


# =========================================================
# SETUP
# =========================================================

def wait_metabase(max_wait_s=300):
    deadline = time.time() + max_wait_s
    while time.time() < deadline:
        try:
            status, _ = request_json("GET", "/api/health", timeout=10)
            if status == 200:
                return
        except Exception:
            pass
        time.sleep(3)
    raise RuntimeError("Metabase no respondio.")


def setup_admin_if_needed():
    status, props = request_json("GET", "/api/session/properties")
    if status != 200 or not isinstance(props, dict):
        raise RuntimeError("Respuesta inesperada.")
    token = props.get("setup-token") or props.get("setup_token")
    if not token:
        print("Metabase ya estaba inicializado.")
        return
    payload = {
        "token": token,
        "user": {"first_name": ADMIN_FIRST, "last_name": ADMIN_LAST, "email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
        "prefs": {"site_name": SITE_NAME, "site_locale": "es", "allow_tracking": False},
    }
    try:
        request_json("POST", "/api/setup", payload)
    except RuntimeError as exc:
        if "HTTP 403" in str(exc):
            print("Metabase ya tenia usuario; continuando.")
            return
        raise
    print(f"Admin creado: {ADMIN_EMAIL}.")


def login():
    _, resp = request_json("POST", "/api/session", {"username": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
    if not isinstance(resp, dict) or "id" not in resp:
        raise RuntimeError("No se pudo iniciar sesion.")
    return str(resp["id"])


def find_by_name(items, name):
    for item in items:
        if item.get("name") == name and not item.get("archived", False):
            return item
    return None


def ensure_database(session_id):
    _, resp = request_json("GET", "/api/database", session_id=session_id)
    dbs = resp.get("data", []) if isinstance(resp, dict) else []
    existing = find_by_name(dbs, DWH_NAME)
    if existing:
        print(f"Base existente: {DWH_NAME} (id={existing['id']}).")
        return int(existing["id"])
    payload = {
        "name": DWH_NAME, "engine": "postgres",
        "details": {"host": DWH_HOST, "port": DWH_PORT, "dbname": DWH_DB, "user": DWH_USER, "password": DWH_PASSWORD, "ssl": False, "schema-filters-type": "inclusion", "schema-filters-patterns": "analytics,staging"},
        "is_full_sync": True, "is_on_demand": False, "schedules": {},
    }
    _, created = request_json("POST", "/api/database", payload, session_id=session_id)
    print(f"Base creada: {DWH_NAME} (id={created['id']}).")
    return int(created["id"])


def ensure_collection(session_id):
    _, cols = request_json("GET", "/api/collection", session_id=session_id)
    existing = find_by_name(cols if isinstance(cols, list) else [], COLLECTION_NAME)
    if existing:
        print(f"Coleccion existente: {COLLECTION_NAME} (id={existing['id']}).")
        return int(existing["id"])
    _, created = request_json("POST", "/api/collection", {"name": COLLECTION_NAME, "description": "Dashboard Amazon E-Commerce Analytics.", "color": C_ORANGE}, session_id=session_id)
    print(f"Coleccion creada: {COLLECTION_NAME} (id={created['id']}).")
    return int(created["id"])


def wait_for_fact_fields(session_id, database_id):
    try:
        request_json("POST", f"/api/database/{database_id}/sync_schema", session_id=session_id)
    except Exception as exc:
        print(f"Aviso sync_schema: {exc}")
    required = ["purchase_date", "category", "location", "device", "payment_method"]
    deadline = time.time() + 180
    while time.time() < deadline:
        _, metadata = request_json("GET", f"/api/database/{database_id}/metadata", session_id=session_id)
        tables = metadata.get("tables", []) if isinstance(metadata, dict) else []
        fact = next((t for t in tables if t.get("schema") == "analytics" and t.get("name") == "fact_orders"), None)
        if fact:
            fields = {f["name"]: int(f["id"]) for f in fact.get("fields", []) if f.get("name") in required}
            if all(n in fields for n in required):
                return fields
        time.sleep(5)
    raise RuntimeError("No se encontraron campos de fact_orders.")


# =========================================================
# FILTROS
# =========================================================

def filter_sql():
    return (
        "WHERE 1 = 1\n"
        "[[AND {{purchase_date}}]]\n"
        "[[AND {{category}}]]\n"
        "[[AND {{location}}]]\n"
        "[[AND {{device}}]]\n"
        "[[AND {{payment_method}}]]"
    )


def template_tags(field_ids):
    return {
        "purchase_date":  {"id": "purchase_date",  "name": "purchase_date",  "display-name": "Fecha de compra", "type": "dimension", "dimension": ["field", field_ids["purchase_date"],  None], "widget-type": "date/all-options"},
        "category":       {"id": "category",        "name": "category",       "display-name": "Categoria",       "type": "dimension", "dimension": ["field", field_ids["category"],       None], "widget-type": "category"},
        "location":       {"id": "location",        "name": "location",       "display-name": "Ciudad",          "type": "dimension", "dimension": ["field", field_ids["location"],       None], "widget-type": "category"},
        "device":         {"id": "device",          "name": "device",         "display-name": "Dispositivo",     "type": "dimension", "dimension": ["field", field_ids["device"],         None], "widget-type": "category"},
        "payment_method": {"id": "payment_method",  "name": "payment_method", "display-name": "Metodo de pago",  "type": "dimension", "dimension": ["field", field_ids["payment_method"], None], "widget-type": "category"},
    }


def base_vis(extra=None):
    """Configuracion visual base con paleta Amazon."""
    vis = {"graph.colors": PALETTE}
    if extra:
        vis.update(extra)
    return vis


# =========================================================
# TABS
# =========================================================

def tab_specs():
    f = filter_sql()
    return [

        # ─────────────────────────────────────────────────
        # TAB 1: RESUMEN — RF1
        # ─────────────────────────────────────────────────
        {"name": "Resumen", "cards": [

            # Fila 1: 5 KPIs compactos size_y=3 para letra mas chica
            {
                "name": "💰 Ingresos Totales", "display": "scalar",
                "row": 0, "col": 0, "size_x": 5, "size_y": 3,
                "visualization_settings": {
                    "scalar.field": "total_revenue",
                    "column_settings": {"[\"name\",\"total_revenue\"]": {"number_style": "currency", "currency": "INR", "currency_style": "symbol", "decimals": 0}},
                },
                "query": f"SELECT ROUND(SUM(final_price)::numeric, 0) AS total_revenue FROM analytics.fact_orders {f}",
            },
            {
                "name": "📦 Total Ordenes", "display": "scalar",
                "row": 0, "col": 5, "size_x": 5, "size_y": 3,
                "visualization_settings": {"scalar.field": "total_orders"},
                "query": f"SELECT COUNT(*) AS total_orders FROM analytics.fact_orders {f}",
            },
            {
                "name": "🎫 Ticket Promedio", "display": "scalar",
                "row": 0, "col": 10, "size_x": 5, "size_y": 3,
                "visualization_settings": {
                    "scalar.field": "avg_ticket",
                    "column_settings": {"[\"name\",\"avg_ticket\"]": {"number_style": "currency", "currency": "INR", "currency_style": "symbol", "decimals": 0}},
                },
                "query": f"SELECT ROUND(AVG(final_price)::numeric, 0) AS avg_ticket FROM analytics.fact_orders {f}",
            },
            {
                "name": "↩️ Tasa Devolucion Pct", "display": "scalar",
                "row": 0, "col": 15, "size_x": 4, "size_y": 3,
                "visualization_settings": {"scalar.field": "return_rate"},
                "query": f"SELECT ROUND(AVG(CASE WHEN is_returned THEN 1.0 ELSE 0.0 END)::numeric * 100, 1) AS return_rate FROM analytics.fact_orders {f}",
            },
            {
                "name": "⭐ Rating Promedio", "display": "scalar",
                "row": 0, "col": 19, "size_x": 5, "size_y": 3,
                "visualization_settings": {"scalar.field": "avg_rating"},
                "query": f"SELECT ROUND(AVG(rating)::numeric, 2) AS avg_rating FROM analytics.fact_orders {f}",
            },

            # Fila 2: evolucion mensual (mas ancha) + tabla variacion pct
            {
                "name": "Evolucion Mensual Resumen", "display": "combo",
                "row": 3, "col": 0, "size_x": 14, "size_y": 7,
                "visualization_settings": {
                    "graph.colors": ["#2E6DA4", "#84BBE3"],
                    "graph.dimensions": ["period_month"],
                    "graph.metrics": ["total_revenue", "total_orders"],
                    "series_settings": {
                        "total_revenue": {"display": "bar",  "color": "#2E6DA4", "axis": "left"},
                        "total_orders":  {"display": "line", "color": "#84BBE3", "axis": "right"},
                    },
                    "graph.x_axis.title_text": "Mes",
                    "graph.y_axis.title_text": "Ingresos (INR)",
                    "graph.show_values": False,
                },
                "query": f"""
SELECT DATE_TRUNC('month', purchase_date)::date AS period_month,
       ROUND(SUM(final_price)::numeric, 0) AS total_revenue,
       COUNT(*) AS total_orders
FROM analytics.fact_orders {f}
GROUP BY 1 ORDER BY period_month
""",
            },
            {
                "name": "Variacion Mensual Tabla", "display": "table",
                "row": 3, "col": 14, "size_x": 10, "size_y": 7,
                "visualization_settings": {
                    "column_settings": {
                        "[\"name\",\"period_month\"]":     {"column_title": "Mes"},
                        "[\"name\",\"total_orders\"]":    {"column_title": "Ordenes"},
                        "[\"name\",\"orders_pct\"]":      {"column_title": "Var%", "number_style": "percent", "decimals": 1, "scale": 0.01},
                        "[\"name\",\"total_revenue\"]":   {"column_title": "Ingresos", "number_style": "currency", "currency": "INR", "decimals": 0},
                        "[\"name\",\"revenue_pct\"]":     {"column_title": "Var%", "number_style": "percent", "decimals": 1, "scale": 0.01},
                        "[\"name\",\"return_rate\"]":     {"column_title": "Dev%"},
                        "[\"name\",\"return_rate_pct\"]": {"column_title": "Var%", "number_style": "percent", "decimals": 1, "scale": 0.01},
                    },
                    "conditional_formatting": [
                        {"color": "#1E8449", "operator": ">", "value": 0, "column": "revenue_pct", "highlight_row": False},
                        {"color": "#C0392B", "operator": "<", "value": 0, "column": "revenue_pct", "highlight_row": False},
                        {"color": "#1E8449", "operator": ">", "value": 0, "column": "orders_pct",  "highlight_row": False},
                        {"color": "#C0392B", "operator": "<", "value": 0, "column": "orders_pct",  "highlight_row": False},
                    ],
                },
                "query": """
SELECT TO_CHAR(period_month, 'Mon YYYY') AS period_month,
       total_orders,
       ROUND(total_orders_pct_change::numeric, 1) AS orders_pct,
       ROUND(total_revenue::numeric, 0) AS total_revenue,
       ROUND(total_revenue_pct_change::numeric, 1) AS revenue_pct,
       ROUND(return_rate::numeric, 1) AS return_rate,
       ROUND(return_rate_pct_change::numeric, 1) AS return_rate_pct
FROM analytics.mart_period_variation
ORDER BY period_month DESC LIMIT 12
""",
            },

            # Fila 3: Categorias (izq) + Torta metodos de pago (der)
            {
                "name": "Ingresos Por Categoria", "display": "row",
                "row": 10, "col": 0, "size_x": 12, "size_y": 7,
                "visualization_settings": {
                    "graph.colors": ["#2E6DA4"],
                    "graph.dimensions": ["category"],
                    "graph.metrics": ["revenue_pct"],
                    "graph.show_values": True,
                    "graph.x_axis.title_text": "% del total de ingresos",
                },
                "query": f"""
SELECT category,
       ROUND(SUM(final_price)::numeric, 0) AS total_revenue,
       ROUND(SUM(final_price) * 100.0 / SUM(SUM(final_price)) OVER (), 1) AS revenue_pct
FROM analytics.fact_orders {f}
GROUP BY category ORDER BY total_revenue DESC
""",
            },
            {
                "name": "Distribucion Metodos De Pago", "display": "pie",
                "row": 10, "col": 12, "size_x": 12, "size_y": 7,
                "visualization_settings": {
                    "graph.colors": ["#1C3F5E", "#2E6DA4", "#84BBE3", "#A9CCE3"],
                    "pie.dimension": "payment_method",
                    "pie.metric": "order_share_pct",
                    "pie.show_legend": True,
                    "pie.show_total": False,
                    "pie.percent_visibility": "inside",
                },
                "query": f"""
SELECT payment_method,
       COUNT(*) AS total_orders,
       ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1) AS order_share_pct,
       ROUND(AVG(CASE WHEN is_returned THEN 1.0 ELSE 0.0 END) * 100, 1) AS return_rate
FROM analytics.fact_orders {f}
GROUP BY payment_method ORDER BY total_orders DESC
""",
            },

            # Fila 4: Estado de entrega (izq) + Dispositivo (der)
            {
                "name": "Ordenes Por Estado De Entrega", "display": "row",
                "row": 17, "col": 0, "size_x": 12, "size_y": 6,
                "visualization_settings": {
                    "graph.colors": ["#1C3F5E"],
                    "graph.dimensions": ["delivery_status"],
                    "graph.metrics": ["order_pct"],
                    "graph.show_values": True,
                    "graph.x_axis.title_text": "% del total de ordenes",
                },
                "query": f"""
SELECT delivery_status,
       COUNT(*) AS total_orders,
       ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1) AS order_pct,
       ROUND(AVG(shipping_time_days)::numeric, 1) AS avg_dias_envio,
       ROUND(AVG(CASE WHEN is_returned THEN 1.0 ELSE 0.0 END) * 100, 1) AS return_rate
FROM analytics.fact_orders {f}
GROUP BY delivery_status ORDER BY total_orders DESC
""",
            },
            {
                "name": "Ordenes Por Dispositivo", "display": "row",
                "row": 17, "col": 12, "size_x": 12, "size_y": 6,
                "visualization_settings": {
                    "graph.colors": ["#84BBE3"],
                    "graph.dimensions": ["device"],
                    "graph.metrics": ["order_pct"],
                    "graph.show_values": True,
                    "graph.x_axis.title_text": "% del total de ordenes",
                },
                "query": f"""
SELECT device,
       COUNT(*) AS total_orders,
       ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1) AS order_pct
FROM analytics.fact_orders {f}
GROUP BY device ORDER BY total_orders DESC
""",
            },
        ]},

        # ─────────────────────────────────────────────────
        # TAB 2: VENTAS — RF3
        # ─────────────────────────────────────────────────
        {"name": "Ventas", "cards": [

            {
                "name": "Evolucion Mensual De Ventas", "display": "line",
                "row": 0, "col": 0, "size_x": COL_FULL, "size_y": H_CHART,
                "visualization_settings": base_vis({
                    "graph.dimensions": ["period_month"],
                    "graph.metrics": ["revenue", "total_orders"],
                    "series_settings": {
                        "revenue":      {"color": C_ORANGE, "axis": "left"},
                        "total_orders": {"color": C_BLUE,   "axis": "right"},
                    },
                    "graph.x_axis.title_text": "Mes",
                    "graph.y_axis.title_text": "Ingresos (USD)",
                    "graph.show_values": False,
                }),
                "query": f"""
SELECT DATE_TRUNC('month', purchase_date)::date AS period_month,
       COUNT(*) AS total_orders,
       ROUND(SUM(final_price)::numeric, 0) AS revenue,
       ROUND(AVG(final_price)::numeric, 2) AS avg_ticket
FROM analytics.fact_orders {f}
GROUP BY 1 ORDER BY period_month
""",
            },
            {
                "name": "Ingresos Por Categoria Y Subcategoria", "display": "bar",
                "row": H_CHART, "col": 0, "size_x": COL_HALF, "size_y": H_CHART,
                "visualization_settings": base_vis({
                    "graph.dimensions": ["category"],
                    "graph.metrics": ["total_revenue"],
                    "graph.show_values": True,
                    "graph.colors": [C_ORANGE],
                    "graph.x_axis.title_text": "Categoria",
                    "graph.y_axis.title_text": "Ingresos (USD)",
                }),
                "query": f"""
SELECT category,
       COUNT(*) AS total_orders,
       ROUND(SUM(final_price)::numeric, 0) AS total_revenue,
       ROUND(AVG(discount)::numeric, 1) AS avg_discount
FROM analytics.fact_orders {f}
GROUP BY category ORDER BY total_revenue DESC
""",
            },
            {
                "name": "Top 15 Marcas Por Ingresos", "display": "row",
                "row": H_CHART, "col": COL_HALF, "size_x": COL_HALF, "size_y": H_CHART,
                "visualization_settings": base_vis({
                    "graph.dimensions": ["brand"],
                    "graph.metrics": ["total_revenue"],
                    "graph.show_values": True,
                    "graph.colors": [C_BLUE],
                }),
                "query": f"""
SELECT brand,
       COUNT(*) AS total_orders,
       ROUND(SUM(final_price)::numeric, 0) AS total_revenue
FROM analytics.fact_orders {f}
GROUP BY brand ORDER BY total_revenue DESC LIMIT 15
""",
            },
            {
                "name": "Relacion Descuento Vs Volumen De Ordenes", "display": "combo",
                "row": H_CHART * 2, "col": 0, "size_x": COL_HALF, "size_y": H_CHART,
                "visualization_settings": base_vis({
                    "graph.dimensions": ["discount_range"],
                    "graph.metrics": ["total_orders", "total_revenue"],
                    "series_settings": {
                        "total_orders":  {"display": "bar",  "color": C_ORANGE, "axis": "left"},
                        "total_revenue": {"display": "line", "color": C_BLUE,   "axis": "right"},
                    },
                    "graph.x_axis.title_text": "Rango de descuento",
                    "graph.show_values": False,
                }),
                "query": f"""
SELECT discount_range, total_orders, total_revenue
FROM analytics.mart_discount_vs_orders
ORDER BY discount_range
""",
            },
            {
                "name": "Ventas Por Dispositivo Y Categoria", "display": "bar",
                "row": H_CHART * 2, "col": COL_HALF, "size_x": COL_HALF, "size_y": H_CHART,
                "visualization_settings": base_vis({
                    "graph.dimensions": ["device", "category"],
                    "graph.metrics": ["total_orders"],
                    "stackable.stack_type": "stacked",
                    "graph.x_axis.title_text": "Dispositivo",
                }),
                "query": f"""
SELECT device, category,
       COUNT(*) AS total_orders,
       ROUND(SUM(final_price)::numeric, 0) AS revenue
FROM analytics.fact_orders {f}
GROUP BY device, category ORDER BY device, revenue DESC
""",
            },
        ]},

        # ─────────────────────────────────────────────────
        # TAB 3: LOGISTICA — RF4
        # ─────────────────────────────────────────────────
        {"name": "Logistica", "cards": [

            # Fila 1: 4 KPIs
            {
                "name": "KPI Entregas A Tiempo", "display": "scalar",
                "row": 0, "col": 0, "size_x": COL_QUARTER, "size_y": H_KPI,
                "visualization_settings": {"scalar.field": "pct_on_time"},
                "query": "SELECT pct_on_time FROM analytics.mart_delivery_performance",
            },
            {
                "name": "KPI Tiempo Promedio Envio", "display": "scalar",
                "row": 0, "col": COL_QUARTER, "size_x": COL_QUARTER, "size_y": H_KPI,
                "visualization_settings": {"scalar.field": "avg_shipping_days"},
                "query": f"SELECT ROUND(AVG(shipping_time_days)::numeric, 1) AS avg_shipping_days FROM analytics.fact_orders {f}",
            },
            {
                "name": "KPI Pedidos Demorados", "display": "scalar",
                "row": 0, "col": COL_QUARTER * 2, "size_x": COL_QUARTER, "size_y": H_KPI,
                "visualization_settings": {"scalar.field": "pct_delayed"},
                "query": "SELECT pct_delayed FROM analytics.mart_delivery_performance",
            },
            {
                "name": "KPI Tasa Devolucion Logistica", "display": "scalar",
                "row": 0, "col": COL_QUARTER * 3, "size_x": COL_QUARTER, "size_y": H_KPI,
                "visualization_settings": {"scalar.field": "return_rate"},
                "query": f"SELECT ROUND(AVG(CASE WHEN is_returned THEN 1.0 ELSE 0.0 END)::numeric * 100, 1) AS return_rate FROM analytics.fact_orders {f}",
            },

            # Fila 2
            {
                "name": "Distribucion Por Estado De Entrega", "display": "bar",
                "row": H_KPI, "col": 0, "size_x": COL_HALF, "size_y": H_CHART,
                "visualization_settings": base_vis({
                    "graph.dimensions": ["delivery_status"],
                    "graph.metrics": ["total_orders"],
                    "graph.show_values": True,
                    "graph.colors": [C_ORANGE],
                    "graph.x_axis.title_text": "Estado de entrega",
                }),
                "query": f"""
SELECT delivery_status,
       COUNT(*) AS total_orders,
       ROUND(AVG(shipping_time_days)::numeric, 1) AS avg_shipping_days,
       ROUND(AVG(CASE WHEN is_returned THEN 1.0 ELSE 0.0 END)::numeric * 100, 1) AS return_rate
FROM analytics.fact_orders {f}
GROUP BY delivery_status ORDER BY total_orders DESC
""",
            },
            {
                "name": "Tiempo Promedio De Envio Por Ciudad", "display": "row",
                "row": H_KPI, "col": COL_HALF, "size_x": COL_HALF, "size_y": H_CHART,
                "visualization_settings": base_vis({
                    "graph.dimensions": ["location"],
                    "graph.metrics": ["avg_shipping_days"],
                    "graph.show_values": True,
                    "graph.colors": [C_BLUE],
                }),
                "query": f"""
SELECT location,
       COUNT(*) AS total_orders,
       ROUND(AVG(shipping_time_days)::numeric, 1) AS avg_shipping_days,
       ROUND(AVG(CASE WHEN is_returned THEN 1.0 ELSE 0.0 END)::numeric * 100, 1) AS return_rate
FROM analytics.fact_orders {f}
GROUP BY location ORDER BY avg_shipping_days DESC
""",
            },

            # Fila 3
            {
                "name": "Tasa De Devolucion Por Categoria", "display": "bar",
                "row": H_KPI + H_CHART, "col": 0, "size_x": COL_THIRD, "size_y": H_CHART,
                "visualization_settings": base_vis({
                    "graph.dimensions": ["category"],
                    "graph.metrics": ["return_rate"],
                    "graph.show_values": True,
                    "graph.colors": [C_RED],
                }),
                "query": f"""
SELECT category,
       ROUND(AVG(CASE WHEN is_returned THEN 1.0 ELSE 0.0 END)::numeric * 100, 1) AS return_rate,
       COUNT(*) AS total_orders
FROM analytics.fact_orders {f}
GROUP BY category ORDER BY return_rate DESC
""",
            },
            {
                "name": "Metodo De Pago Vs Devolucion", "display": "bar",
                "row": H_KPI + H_CHART, "col": COL_THIRD, "size_x": COL_THIRD, "size_y": H_CHART,
                "visualization_settings": base_vis({
                    "graph.dimensions": ["payment_method"],
                    "graph.metrics": ["return_rate"],
                    "graph.show_values": True,
                    "graph.colors": [C_ORANGE2],
                }),
                "query": f"""
SELECT payment_method, return_rate, total_orders, returned_orders
FROM analytics.mart_payment_vs_returns
ORDER BY return_rate DESC
""",
            },
            {
                "name": "Tendencia Mensual Pedidos Demorados", "display": "line",
                "row": H_KPI + H_CHART, "col": COL_THIRD * 2, "size_x": COL_THIRD, "size_y": H_CHART,
                "visualization_settings": base_vis({
                    "graph.dimensions": ["period_month"],
                    "graph.metrics": ["delayed_rate"],
                    "graph.colors": [C_RED],
                    "graph.x_axis.title_text": "Mes",
                    "graph.y_axis.title_text": "% Demorados",
                }),
                "query": f"""
SELECT DATE_TRUNC('month', purchase_date)::date AS period_month,
       ROUND(AVG(CASE WHEN delivery_status = 'Delayed' THEN 1.0 ELSE 0.0 END)::numeric * 100, 1) AS delayed_rate
FROM analytics.fact_orders {f}
GROUP BY 1 ORDER BY period_month
""",
            },

            # Fila 4: demoras vs devoluciones
            {
                "name": "Dias De Envio Vs Tasa De Devolucion", "display": "line",
                "row": H_KPI + H_CHART * 2, "col": 0, "size_x": COL_FULL, "size_y": H_CHART,
                "visualization_settings": base_vis({
                    "graph.dimensions": ["shipping_time_days"],
                    "graph.metrics": ["return_rate", "total_orders"],
                    "series_settings": {
                        "return_rate":  {"color": C_RED,    "axis": "left"},
                        "total_orders": {"color": C_ORANGE, "axis": "right"},
                    },
                    "graph.x_axis.title_text": "Dias de envio",
                    "graph.y_axis.title_text": "Tasa de devolucion (%)",
                }),
                "query": """
SELECT shipping_time_days, total_orders, returned_orders, return_rate
FROM analytics.mart_delays_vs_returns
ORDER BY shipping_time_days
""",
            },
        ]},

        # ─────────────────────────────────────────────────
        # TAB 4: CLIENTES — RF5
        # ─────────────────────────────────────────────────
        {"name": "Clientes", "cards": [

            {
                "name": "KPI Rating Promedio", "display": "scalar",
                "row": 0, "col": 0, "size_x": COL_HALF, "size_y": H_KPI,
                "visualization_settings": {"scalar.field": "avg_rating"},
                "query": f"SELECT ROUND(AVG(rating)::numeric, 2) AS avg_rating FROM analytics.fact_orders {f}",
            },
            {
                "name": "KPI Devolucion Global", "display": "scalar",
                "row": 0, "col": COL_HALF, "size_x": COL_HALF, "size_y": H_KPI,
                "visualization_settings": {"scalar.field": "return_rate"},
                "query": f"SELECT ROUND(AVG(CASE WHEN is_returned THEN 1.0 ELSE 0.0 END)::numeric * 100, 1) AS return_rate FROM analytics.fact_orders {f}",
            },
            {
                "name": "Distribucion De Ratings", "display": "bar",
                "row": H_KPI, "col": 0, "size_x": COL_HALF, "size_y": H_CHART,
                "visualization_settings": base_vis({
                    "graph.dimensions": ["rating"],
                    "graph.metrics": ["total_orders"],
                    "graph.colors": [C_ORANGE],
                    "graph.show_values": False,
                    "graph.x_axis.title_text": "Rating",
                    "graph.y_axis.title_text": "Ordenes",
                }),
                "query": """
SELECT rating, total_orders, order_share_pct
FROM analytics.mart_rating_distribution
ORDER BY rating
""",
            },
            {
                "name": "Rating Por Rango", "display": "row",
                "row": H_KPI, "col": COL_HALF, "size_x": COL_HALF, "size_y": H_CHART,
                "visualization_settings": base_vis({
                    "graph.dimensions": ["rating_range"],
                    "graph.metrics": ["total_orders"],
                    "graph.show_values": True,
                    "graph.colors": [C_BLUE],
                }),
                "query": """
SELECT rating_range, total_orders, order_share_pct, avg_rating, return_rate
FROM analytics.mart_rating_by_range
ORDER BY rating_range
""",
            },
            {
                "name": "Rating Por Categoria", "display": "bar",
                "row": H_KPI + H_CHART, "col": 0, "size_x": COL_HALF, "size_y": H_CHART,
                "visualization_settings": base_vis({
                    "graph.dimensions": ["category"],
                    "graph.metrics": ["avg_rating", "return_rate"],
                    "series_settings": {
                        "avg_rating":  {"color": C_ORANGE, "axis": "left"},
                        "return_rate": {"color": C_RED,    "axis": "right"},
                    },
                    "graph.x_axis.title_text": "Categoria",
                }),
                "query": f"""
SELECT category,
       ROUND(AVG(rating)::numeric, 2) AS avg_rating,
       ROUND(AVG(CASE WHEN is_returned THEN 1.0 ELSE 0.0 END)::numeric * 100, 1) AS return_rate,
       COUNT(*) AS total_orders
FROM analytics.fact_orders {f}
GROUP BY category ORDER BY avg_rating DESC
""",
            },
            {
                "name": "Satisfaccion Por Ciudad", "display": "row",
                "row": H_KPI + H_CHART, "col": COL_HALF, "size_x": COL_HALF, "size_y": H_CHART,
                "visualization_settings": base_vis({
                    "graph.dimensions": ["location"],
                    "graph.metrics": ["avg_rating"],
                    "graph.show_values": True,
                    "graph.colors": [C_GREEN],
                }),
                "query": f"""
SELECT location,
       ROUND(AVG(rating)::numeric, 2) AS avg_rating,
       COUNT(*) AS total_orders,
       ROUND(AVG(CASE WHEN is_returned THEN 1.0 ELSE 0.0 END)::numeric * 100, 1) AS return_rate
FROM analytics.fact_orders {f}
GROUP BY location ORDER BY avg_rating DESC
""",
            },
            {
                "name": "Impacto Tiempo De Envio En Satisfaccion", "display": "line",
                "row": H_KPI + H_CHART * 2, "col": 0, "size_x": COL_HALF, "size_y": H_CHART,
                "visualization_settings": base_vis({
                    "graph.dimensions": ["shipping_time_days"],
                    "graph.metrics": ["avg_rating"],
                    "graph.colors": [C_ORANGE],
                    "graph.x_axis.title_text": "Dias de envio",
                    "graph.y_axis.title_text": "Rating promedio",
                }),
                "query": f"""
SELECT shipping_time_days,
       ROUND(AVG(rating)::numeric, 2) AS avg_rating,
       COUNT(*) AS total_orders
FROM analytics.fact_orders {f}
GROUP BY shipping_time_days ORDER BY shipping_time_days
""",
            },
            {
                "name": "Comportamiento Por Dispositivo", "display": "bar",
                "row": H_KPI + H_CHART * 2, "col": COL_HALF, "size_x": COL_HALF, "size_y": H_CHART,
                "visualization_settings": base_vis({
                    "graph.dimensions": ["device"],
                    "graph.metrics": ["total_orders", "avg_rating"],
                    "series_settings": {
                        "total_orders": {"color": C_BLUE,   "axis": "left"},
                        "avg_rating":   {"color": C_ORANGE, "axis": "right"},
                    },
                    "graph.x_axis.title_text": "Dispositivo",
                }),
                "query": f"""
SELECT device,
       COUNT(*) AS total_orders,
       ROUND(AVG(rating)::numeric, 2) AS avg_rating,
       ROUND(AVG(CASE WHEN is_returned THEN 1.0 ELSE 0.0 END)::numeric * 100, 1) AS return_rate
FROM analytics.fact_orders {f}
GROUP BY device ORDER BY total_orders DESC
""",
            },
        ]},

        # ─────────────────────────────────────────────────
        # TAB 5: VENDEDORES — RF6
        # ─────────────────────────────────────────────────
        {"name": "Vendedores", "cards": [

            {
                "name": "KPI Vendedores Activos", "display": "scalar",
                "row": 0, "col": 0, "size_x": COL_HALF, "size_y": H_KPI,
                "visualization_settings": {"scalar.field": "total_vendedores"},
                "query": f"SELECT COUNT(DISTINCT seller_id) AS total_vendedores FROM analytics.fact_orders {f}",
            },
            {
                "name": "KPI Rating Promedio Vendedores", "display": "scalar",
                "row": 0, "col": COL_HALF, "size_x": COL_HALF, "size_y": H_KPI,
                "visualization_settings": {"scalar.field": "avg_seller_rating"},
                "query": f"SELECT ROUND(AVG(seller_rating)::numeric, 2) AS avg_seller_rating FROM analytics.fact_orders {f}",
            },
            {
                "name": "Ranking Vendedores Por Ingresos", "display": "table",
                "row": H_KPI, "col": 0, "size_x": COL_FULL, "size_y": H_TABLE,
                "visualization_settings": {
                    "graph.colors": PALETTE,
                    "column_settings": {
                        "[\"name\",\"total_revenue\"]": {"number_style": "currency", "currency": "USD", "decimals": 0},
                        "[\"name\",\"return_rate\"]":   {"number_style": "percent",  "decimals": 1, "scale": 0.01},
                    },
                    "conditional_formatting": [
                        {"color": C_RED,   "operator": ">", "value": 15, "column": "return_rate", "highlight_row": False},
                        {"color": C_GREEN, "operator": "<", "value": 5,  "column": "return_rate", "highlight_row": False},
                    ],
                },
                "query": f"""
SELECT seller_id,
       COUNT(*) AS total_orders,
       ROUND(SUM(final_price)::numeric, 0) AS total_revenue,
       ROUND(AVG(final_price)::numeric, 2) AS avg_ticket,
       ROUND(AVG(seller_rating)::numeric, 2) AS avg_seller_rating,
       ROUND(AVG(CASE WHEN is_returned THEN 1.0 ELSE 0.0 END)::numeric * 100, 1) AS return_rate
FROM analytics.fact_orders {f}
GROUP BY seller_id ORDER BY total_revenue DESC LIMIT 50
""",
            },
            {
                "name": "Rating Vs Devolucion Por Vendedor", "display": "scatter",
                "row": H_KPI + H_TABLE, "col": 0, "size_x": COL_HALF, "size_y": H_CHART,
                "visualization_settings": base_vis({
                    "graph.dimensions": ["avg_seller_rating"],
                    "graph.metrics": ["return_rate"],
                    "graph.colors": [C_ORANGE],
                }),
                "query": f"""
SELECT seller_id,
       COUNT(*) AS total_orders,
       ROUND(SUM(final_price)::numeric, 0) AS total_revenue,
       ROUND(AVG(seller_rating)::numeric, 2) AS avg_seller_rating,
       ROUND(AVG(CASE WHEN is_returned THEN 1.0 ELSE 0.0 END)::numeric * 100, 1) AS return_rate
FROM analytics.fact_orders {f}
GROUP BY seller_id HAVING COUNT(*) >= 10
ORDER BY total_revenue DESC
""",
            },
            {
                "name": "Categorias Por Vendedor Top 50", "display": "table",
                "row": H_KPI + H_TABLE, "col": COL_HALF, "size_x": COL_HALF, "size_y": H_CHART,
                "visualization_settings": {
                    "graph.colors": PALETTE,
                    "column_settings": {
                        "[\"name\",\"total_revenue\"]": {"number_style": "currency", "currency": "USD", "decimals": 0},
                    },
                },
                "query": f"""
SELECT seller_id, category, total_orders, total_revenue, return_rate
FROM analytics.mart_categories_by_seller
ORDER BY seller_id, total_revenue DESC
LIMIT 100
""",
            },
            {
                "name": "Vendedores Con Mayor Tasa De Devolucion", "display": "table",
                "row": H_KPI + H_TABLE + H_CHART, "col": 0, "size_x": COL_FULL, "size_y": H_TABLE,
                "visualization_settings": {
                    "graph.colors": PALETTE,
                    "conditional_formatting": [
                        {"color": C_RED, "operator": ">", "value": 15, "column": "return_rate", "highlight_row": False},
                    ],
                },
                "query": f"""
SELECT seller_id,
       COUNT(*) AS total_orders,
       ROUND(SUM(final_price)::numeric, 0) AS total_revenue,
       ROUND(AVG(seller_rating)::numeric, 2) AS avg_seller_rating,
       ROUND(AVG(CASE WHEN is_returned THEN 1.0 ELSE 0.0 END)::numeric * 100, 1) AS return_rate
FROM analytics.fact_orders {f}
GROUP BY seller_id HAVING COUNT(*) >= 10
ORDER BY return_rate DESC LIMIT 25
""",
            },
        ]},

        # ─────────────────────────────────────────────────
        # TAB 6: GLOSARIO — RF9
        # ─────────────────────────────────────────────────
        {"name": "Glosario", "cards": [
            {
                "name": "Glosario De KPIs E Indicadores", "display": "table",
                "row": 0, "col": 0, "size_x": COL_FULL, "size_y": 20,
                "visualization_settings": {},
                "query": """
SELECT kpi, formula, interpretacion FROM (VALUES
  ('Ingresos Totales',         'SUM(final_price)',                                                   'Suma de todos los ingresos del periodo. Cada fila representa 1 orden = 1 unidad vendida.'),
  ('Total Ordenes',            'COUNT(*)',                                                           'Cantidad total de ordenes. Equivale a unidades vendidas ya que cada fila es una orden.'),
  ('Ticket Promedio',          'AVG(final_price)',                                                   'Ingreso promedio por orden. Indica el valor medio de cada transaccion.'),
  ('Tasa De Devolucion',       'SUM(is_returned) / COUNT(*) * 100',                                 'Porcentaje de ordenes devueltas. Valores altos pueden indicar problemas de calidad o logistica.'),
  ('Rating Promedio',          'AVG(rating)',                                                        'Calificacion promedio de productos (escala 1 a 5). Refleja la satisfaccion del cliente.'),
  ('Pct Entregas A Tiempo',    'delivery_status = Delivered / COUNT(*) * 100',                      'Porcentaje de pedidos entregados exitosamente sin demoras.'),
  ('Pct Pedidos Demorados',    'delivery_status = Delayed / COUNT(*) * 100',                        'Porcentaje de pedidos con demoras en la entrega.'),
  ('Tiempo Promedio Envio',    'AVG(shipping_time_days)',                                            'Promedio de dias desde la compra hasta la entrega.'),
  ('Rating Vendedor',          'AVG(seller_rating)',                                                 'Calificacion promedio de los vendedores (escala 1 a 5).'),
  ('Variacion Pct',            '(valor_actual - valor_anterior) / valor_anterior * 100',             'Cambio porcentual respecto al periodo anterior. Positivo indica crecimiento.'),
  ('Unidades Vendidas',        'COUNT(*)',                                                           'Cada fila del dataset representa una orden de 1 unidad. No existe columna de cantidad.')
) AS t(kpi, formula, interpretacion)
""",
            },
        ]},
    ]


# =========================================================
# CARDS
# =========================================================

def ensure_card(session_id, database_id, collection_id, card_spec, tags, existing_cards):
    vis = {k: v for k, v in card_spec.get("visualization_settings", {}).items()}
    payload = {
        "name": card_spec["name"],
        "description": "Pregunta SQL — Amazon E-Commerce Analytics.",
        "collection_id": collection_id,
        "display": card_spec["display"],
        "dataset_query": {
            "database": database_id,
            "type": "native",
            "native": {"query": card_spec["query"].strip(), "template-tags": tags},
        },
        "visualization_settings": vis,
    }
    existing = existing_cards.get(card_spec["name"])
    if existing:
        request_json("PUT", f"/api/card/{existing['id']}", payload, session_id=session_id)
        return int(existing["id"])
    _, created = request_json("POST", "/api/card", payload, session_id=session_id)
    return int(created["id"])


def list_cards(session_id):
    _, resp = request_json("GET", "/api/card", session_id=session_id)
    cards = resp if isinstance(resp, list) else resp.get("data", [])
    return {c["name"]: c for c in cards if not c.get("archived", False)}


# =========================================================
# DASHBOARD CON TABS
# =========================================================

def ensure_single_dashboard(session_id, collection_id):
    _, resp = request_json("GET", "/api/dashboard", session_id=session_id)
    dashboards = resp.get("data", []) if isinstance(resp, dict) else resp
    existing = find_by_name(dashboards if isinstance(dashboards, list) else [], DASHBOARD_NAME)
    payload = {"name": DASHBOARD_NAME, "description": "Dashboard Amazon E-Commerce Analytics — RF1 a RF9.", "collection_id": collection_id}
    if existing:
        dashboard_id = int(existing["id"])
        request_json("PUT", f"/api/dashboard/{dashboard_id}", payload, session_id=session_id)
        print(f"Dashboard existente: {DASHBOARD_NAME} (id={dashboard_id}).")
    else:
        _, created = request_json("POST", "/api/dashboard", payload, session_id=session_id)
        dashboard_id = int(created["id"])
        print(f"Dashboard creado: {DASHBOARD_NAME} (id={dashboard_id}).")
    return dashboard_id


def create_tabs_and_build(session_id, dashboard_id, tabs_data, card_name_to_id):
    """Crea tabs y layout en un solo PUT — compatible con Metabase v0.49."""
    parameters = [
        {"id": "purchase_date",  "name": "Fecha de compra", "slug": "purchase_date",  "type": "date/all-options", "sectionId": "date"},
        {"id": "category",       "name": "Categoria",       "slug": "category",       "type": "category",         "sectionId": "string"},
        {"id": "location",       "name": "Ciudad",          "slug": "location",       "type": "category",         "sectionId": "string"},
        {"id": "device",         "name": "Dispositivo",     "slug": "device",         "type": "category",         "sectionId": "string"},
        {"id": "payment_method", "name": "Metodo de pago",  "slug": "payment_method", "type": "category",         "sectionId": "string"},
    ]
    tabs = [{"id": -(idx + 1), "name": tab["name"], "position": idx} for idx, tab in enumerate(tabs_data)]
    dashcards = []
    dashcard_id = -1
    for tab_idx, tab_data in enumerate(tabs_data):
        tab_temp_id = -(tab_idx + 1)
        for card_spec in tab_data["cards"]:
            card_id = card_name_to_id.get(card_spec["name"])
            if not card_id:
                print(f"  AVISO: card no encontrada: {card_spec['name']}")
                continue
            dashcards.append({
                "id": dashcard_id, "card_id": card_id,
                "dashboard_tab_id": tab_temp_id,
                "row": card_spec["row"], "col": card_spec["col"],
                "size_x": card_spec["size_x"], "size_y": card_spec["size_y"],
                "visualization_settings": {},
                "parameter_mappings": [
                    {"parameter_id": p["id"], "card_id": card_id, "target": ["dimension", ["template-tag", p["id"]]]}
                    for p in parameters
                ],
            })
            dashcard_id -= 1
    request_json("PUT", f"/api/dashboard/{dashboard_id}", {"parameters": parameters, "tabs": tabs, "dashcards": dashcards}, session_id=session_id)
    print(f"Dashboard: {len(tabs)} tabs, {len(dashcards)} tarjetas.")


# build_dashboard_with_tabs reemplazada por create_tabs_and_build


# =========================================================
# MAIN
# =========================================================

def main():
    print("Esperando a Metabase...")
    wait_metabase()
    setup_admin_if_needed()
    session_id = login()

    print("Configurando base de datos...")
    database_id = ensure_database(session_id)

    print("Configurando coleccion...")
    collection_id = ensure_collection(session_id)

    print("Sincronizando campos de fact_orders...")
    field_ids = wait_for_fact_fields(session_id, database_id)
    tags = template_tags(field_ids)

    print("Creando preguntas SQL...")
    existing_cards = list_cards(session_id)
    tabs = tab_specs()

    card_name_to_id = {}
    for tab in tabs:
        for card_spec in tab["cards"]:
            card_id = ensure_card(session_id, database_id, collection_id, card_spec, tags, existing_cards)
            card_name_to_id[card_spec["name"]] = card_id
            existing_cards[card_spec["name"]] = {"id": card_id}
            print(f"  Card: {card_spec['name']} (id={card_id})")

    print(f"Total: {len(card_name_to_id)} preguntas.")

    print("Creando dashboard principal...")
    dashboard_id = ensure_single_dashboard(session_id, collection_id)

    print("Creando tabs y construyendo layout...")
    create_tabs_and_build(session_id, dashboard_id, tabs, card_name_to_id)

    print(f"\nMetabase provisionado correctamente.")
    print(f"Dashboard: http://localhost:3000/dashboard/{dashboard_id}")
    print(f"Tabs: {', '.join(tab_names)}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc