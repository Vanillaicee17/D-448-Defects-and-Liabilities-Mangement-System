import requests
import os

OLLAMA_URL = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
MODEL = os.getenv("OLLAMA_MODEL", "sqlcoder:7b")


def generate_sql(question: str, schema: str) -> str:
    prompt = f"""
You are a SQL expert for a vessel defect management system.

Schema:
{schema}

Rules:
- Only generate SELECT queries
- No INSERT, UPDATE, DELETE, DROP
- No explanations
- Always include LIMIT 100

Question: {question}
"""

    response = requests.post(
        f"{OLLAMA_URL}/api/generate",
        json={
            "model": MODEL,
            "prompt": prompt,
            "stream": False
        }
    )

    return response.json()["response"].strip()
