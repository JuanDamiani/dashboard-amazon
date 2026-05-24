"""
Conexion reutilizable al Data Warehouse PostgreSQL.

Centraliza la creacion del engine SQLAlchemy usado por validaciones, cargas,
transformaciones, KPIs y auditoria. Apoya RNF-10 porque evita repetir logica de
conexion en cada script y mantiene el pipeline mas mantenible.
"""

from sqlalchemy import create_engine
from scripts.config import DB_URL

engine = create_engine(DB_URL)
