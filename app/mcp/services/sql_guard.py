import sqlparse

FORBIDDEN = {"INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "TRUNCATE"}


def validate_sql(query: str) -> str:
    parsed = sqlparse.parse(query)

    if not parsed:
        raise ValueError("Invalid SQL")

    statement = parsed[0]
    tokens = [t.value.upper() for t in statement.tokens]

    full_query = " ".join(tokens)

    for word in FORBIDDEN:
        if word in full_query:
            raise ValueError(f"Forbidden SQL detected: {word}")

    if not query.strip().lower().startswith("select"):
        raise ValueError("Only SELECT queries allowed")

    if "limit" not in query.lower():
        query += " LIMIT 100"

    return query
