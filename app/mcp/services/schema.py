from sqlalchemy import create_engine, inspect
import os

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)


def get_schema_text():
    inspector = inspect(engine)
    schema = ""

    for table in inspector.get_table_names():
        schema += f"\nTable: {table}\n"

        for col in inspector.get_columns(table):
            schema += f"  - {col['name']} ({col['type']})\n"

    return schema
