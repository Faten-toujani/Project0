"""The one prompt. Identical for all three models - no per-model variants.

Frozen after dev-set debugging; not changed after seeing any test result.
"""
from pathlib import Path

SCHEMA = (Path(__file__).resolve().parent.parent / "data" / "schema.sql").read_text()

TEMPLATE = """You are a SQL generator for a SQLite database.

Schema:
{schema}

Rules:
- Answer with exactly one SQLite SELECT statement.
- Output the SQL and nothing else: no explanation, no comments, no markdown, no code fences.
- Use only tables and columns that appear in the schema above.

Question: {question}"""

MAX_OUTPUT_TOKENS = 1000
TEMPERATURE = 0


def build(question: str) -> str:
    return TEMPLATE.format(schema=SCHEMA.strip(), question=question)
