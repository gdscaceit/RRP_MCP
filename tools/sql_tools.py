# tools/sql_tools.py

import re
from typing import Dict, Any
from RRP_MCP.database import engine
from tools.schema_tool import get_detailed_schema

from langchain_google_vertexai import ChatVertexAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain


# ---------- LLM MODEL (GOOGLE GEMINI via LANGCHAIN) ----------
llm = ChatVertexAI(
    model="gemini-1.5-flash",
    temperature=0,
    max_output_tokens=512,
)


# ---------- PROMPT TEMPLATE ----------
SQL_PROMPT = PromptTemplate(
    input_variables=["schema", "question"],
    template="""
You are an expert SQL generator for PostgreSQL.
You MUST return ONLY one single SQL SELECT query.
No explanation. No markdown. No backticks.

Rules:
- Use exact column names.
- Use JOINs when required.
- Only return pure SQL.
- Do NOT include comments.

Database Schema:
{schema}

User Question:
{question}

Return ONLY the SQL SELECT query:
""",
)


chain = LLMChain(llm=llm, prompt=SQL_PROMPT)


# ---------- FUNCTION: Convert Natural Language → SQL ----------
def nl_to_sql_via_llm(user_query: str, schema: Dict[str, Any]) -> Dict[str, Any]:
    try:
        # Build schema text
        schema_text = []
        for table, meta in schema.items():
            cols = ", ".join([c["name"] for c in meta["columns"]])
            schema_text.append(f"{table}: {cols}")

        schema_string = "\n".join(schema_text)

        # Run LLM chain
        sql = chain.run(schema=schema_string, question=user_query).strip()

        # cleanup
        sql = sql.replace("```sql", "").replace("```", "").strip()

        return {"sql": sql}

    except Exception as e:
        return {"error": f"LangChain/Gemini Error: {str(e)}"}
    


# ---------- SAFETY ----------
_SQL_SELECT_RE = re.compile(r'^\s*select\b', re.IGNORECASE)

def is_safe_select_query(query: str) -> bool:
    q = query.strip()

    if ";" in q:
        return False

    if not _SQL_SELECT_RE.match(q):
        return False

    forbidden = ["drop ", "delete ", "truncate ", "alter ", "update ", "insert ", "create "]
    lower = q.lower()

    if any(k in lower for k in forbidden):
        return False

    return True


# ---------- RUN SQL ----------
def run_sql(query: str, allow_write: bool = False):
    if not allow_write and not is_safe_select_query(query):
        return {"error": "Only safe SELECT queries allowed."}

    try:
        with engine.connect() as conn:
            result = conn.execute(query)
            rows = [dict(row) for row in result]
            return {"rows": rows}
    except Exception as e:
        return {"error": str(e)}
