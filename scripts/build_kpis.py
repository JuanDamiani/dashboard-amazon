"""
Orquestador compatible para construir todos los KPIs.

El DAG ejecuta cada KPI en una tarea separada y en paralelo cuando es posible,
pero este archivo permite reconstruir todos los marts desde un unico comando.
Apoya RF1 a RF6 porque agrupa las metricas que alimentan las paginas del
dashboard: resumen, ventas, logistica, experiencia de cliente y vendedores.
"""

from datetime import datetime

# KPIs originales
from scripts.kpis.customer_experience import build_customer_experience
from scripts.kpis.device_sales import build_device_sales
from scripts.kpis.logistics import build_logistics
from scripts.kpis.logistics_by_city import build_logistics_by_city
from scripts.kpis.monthly_delays import build_monthly_delays
from scripts.kpis.monthly_sales import build_monthly_sales
from scripts.kpis.payment_methods import build_payment_methods
from scripts.kpis.period_variation import build_period_variation
from scripts.kpis.returns import build_returns
from scripts.kpis.sales_by_brand import build_sales_by_brand
from scripts.kpis.sales_by_category import build_sales_by_category
from scripts.kpis.sales_summary import build_sales_summary
from scripts.kpis.satisfaction_by_city import build_satisfaction_by_city
from scripts.kpis.seller_performance import build_seller_performance

# KPIs nuevos — cubren los faltantes del SRS
from scripts.kpis.delivery_performance import build_delivery_performance
from scripts.kpis.payment_vs_returns import build_payment_vs_returns
from scripts.kpis.delays_vs_returns import build_delays_vs_returns
from scripts.kpis.rating_distribution import build_rating_distribution
from scripts.kpis.categories_by_seller import build_categories_by_seller
from scripts.kpis.discount_vs_orders import build_discount_vs_orders


KPI_BUILDERS = [
    # KPIs originales
    build_sales_summary,        # RF1
    build_sales_by_category,    # RF1, RF3
    build_sales_by_brand,       # RF3
    build_logistics,            # RF1, RF4
    build_payment_methods,      # RF1
    build_returns,              # RF4, RF5
    build_monthly_sales,        # RF3
    build_device_sales,         # RF1, RF3, RF5
    build_customer_experience,  # RF5
    build_satisfaction_by_city, # RF5
    build_seller_performance,   # RF6
    build_logistics_by_city,    # RF4
    build_monthly_delays,       # RF4
    build_period_variation,     # RF1, RF3

    # KPIs nuevos
    build_delivery_performance, # RF4: % entregas a tiempo, % demorados
    build_payment_vs_returns,   # RF4: metodo de pago vs devolucion
    build_delays_vs_returns,    # RF4: demoras vs devoluciones
    build_rating_distribution,  # RF5: distribucion ratings y rating por rango
    build_categories_by_seller, # RF6: categorias por vendedor
    build_discount_vs_orders,   # RF3: descuento vs volumen ordenes
]


def build_kpis():
    """Compatibility entrypoint to rebuild every mart in sequence."""
    print("=" * 50)
    print("Inicio build KPIs")
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)

    for builder in KPI_BUILDERS:
        builder()

    print("=" * 50)
    print("Build KPIs finalizado")
    print("=" * 50)


if __name__ == "__main__":
    build_kpis()
