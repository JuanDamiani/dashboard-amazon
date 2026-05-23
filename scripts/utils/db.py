from sqlalchemy import create_engine
from scripts.config import DB_URL

engine = create_engine(DB_URL)