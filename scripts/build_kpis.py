"""
Orquestador compatible para construir todos los KPIs.

El DAG ejecuta cada KPI en una tarea separada y en paralelo cuando es posible,
pero este archivo permite reconstruir todos los marts desde un unico comando.
Apoya RF1 a RF6 porque agrupa las metricas que alimentan las paginas del
dashboard: resumen, ventas, logistica, experiencia de cliente y vendedores.
"""

from datetime import datetime

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


KPI_BUILDERS = [
    build_sales_summary,
    build_sales_by_category,
    build_sales_by_brand,
    build_logistics,
    build_payment_methods,
    build_returns,
    build_monthly_sales,
    build_device_sales,
    build_customer_experience,
    build_satisfaction_by_city,
    build_seller_performance,
    build_logistics_by_city,
    build_monthly_delays,
    build_period_variation,
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
