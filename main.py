# main.py
from fastmcp import FastMCP
from RRP_MCP.database import Base, engine
from tools.schema_tool import get_detailed_schema
from tools.sql_tools import nl_to_sql_via_llm, run_sql
from RRP_MCP.model import Manager, Project, Interview, Payment

# create tables
Base.metadata.create_all(bind=engine)

mcp = FastMCP("Golden Eagle Sales MCP 🚀")

# Tool: return detailed schema (useful to LLM & debugging)
@mcp.tool
def get_schema(limit_sample_rows: int = 3) -> dict:
    """
    Returns the DB schema (tables, columns, FKs, sample rows).
    """
    return get_detailed_schema(limit_sample_rows=limit_sample_rows)

# Tool: NL -> SQL prompt or SQL via OpenAI (if configured)
@mcp.tool
def nl_to_sql(user_query: str) -> dict:
    """
    Returns either:
     - {'prompt_for_llm': <big prompt>} (if no OPENAI key),
     - {'sql': '<generated sql>'} (if we called LLM)
    """
    schema = get_detailed_schema(limit_sample_rows=2)
    return nl_to_sql_via_llm(user_query, schema)

# Tool: run SQL (safe exec)
@mcp.tool
def execute_sql(query: str, allow_write: bool = False) -> dict:
    return run_sql(query, allow_write=allow_write)

# Coordinator: full flow — NL -> SQL -> Exec
@mcp.tool
def query_coordinator(user_query: str) -> dict:
    """
    Full flow: create prompt, get SQL (or LLM prompt), and execute if SQL provided.
    """
    schema = get_detailed_schema(limit_sample_rows=2)
    res = nl_to_sql_via_llm(user_query, schema)
    if "sql" in res:
        # Execute the SQL and return results
        exec_res = run_sql(res["sql"])
        return {
            "sql": res["sql"],
            "result": exec_res
        }
    else:
        # No automatic SQL produced (e.g. no OPENAI key) -> return prompt for dev to use
        return res

if __name__ == "__main__":
    mcp.run()
