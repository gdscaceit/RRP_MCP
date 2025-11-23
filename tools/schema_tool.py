# tools/schema_tool.py
from sqlalchemy import inspect
from RRP_MCP.database import engine

def get_detailed_schema(limit_sample_rows: int = 3) -> dict:
    """
    Returns detailed DB schema: tables -> columns (name, type, nullable, pk),
    foreign keys and a few sample rows for context.
    """
    inspector = inspect(engine)
    schema = {}
    for table_name in inspector.get_table_names():
        cols = []
        for col in inspector.get_columns(table_name):
            cols.append({
                "name": col["name"],
                "type": str(col["type"]),
                "nullable": col.get("nullable", True),
                "default": col.get("default", None),
                "primary_key": col.get("primary_key", False),
            })
        fks = []
        for fk in inspector.get_foreign_keys(table_name):
            fks.append({
                "constrained_columns": fk.get("constrained_columns"),
                "referred_table": fk.get("referred_table"),
                "referred_columns": fk.get("referred_columns")
            })

        # sample rows
        sample = []
        try:
            with engine.connect() as conn:
                res = conn.execute(f"SELECT * FROM {table_name} LIMIT {limit_sample_rows}")
                sample = [dict(row) for row in res]
        except Exception:
            sample = []

        schema[table_name] = {
            "columns": cols,
            "foreign_keys": fks,
            "sample_rows": sample
        }
    return schema
