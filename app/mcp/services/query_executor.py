from sqlalchemy import create_engine, text
import os

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)


def execute_query(sql: str):
    with engine.connect() as conn:
        result = conn.execute(text(sql))
        rows = result.fetchall()
        return [dict(row._mapping) for row in rows]
