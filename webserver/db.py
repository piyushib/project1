from local_config import DATABASE_URI, SHA_SALT
from sqlalchemy import create_engine, MetaData
from sqlalchemy.sql import text
from contextlib import contextmanager

engine = create_engine(DATABASE_URI)
metadata = MetaData(bind=engine)

@contextmanager
def db_conn():
    conn = engine.connect()
    try:
        yield conn
    finally:
        conn.close()

@contextmanager
def db_query_one(querystr, *args, **kwargs):
    conn = engine.connect()
    cursor = conn.execute(text(querystr), *args, **kwargs)
    try:
        yield cursor
    finally:
        conn.close()
