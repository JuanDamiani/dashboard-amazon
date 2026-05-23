from sqlalchemy import create_engine
from scripts.config import DB_URL

# Engine se crea una sola vez cuando se importa el módulo
_engine = None

def get_engine():
    """
    Retorna la conexión a PostgreSQL.
    La crea solo la primera vez y la reutiliza.
    """
    global _engine
    if _engine is None:
        _engine = create_engine(DB_URL)
    return _engine


def cargar_tabla(df, tabla, schema):
    """
    Carga un dataframe en una tabla de PostgreSQL.
    Reemplaza los datos existentes en cada ejecución.
    """
    engine = get_engine()
    df.to_sql(
        tabla,
        engine,
        schema=schema,
        if_exists="replace",
        index=False
    )
    print(f"Carga completada: {len(df):,} filas en {schema}.{tabla}")