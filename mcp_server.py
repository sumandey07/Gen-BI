import re
from typing import List, Dict, Any
import sqlite3
from http import HTTPStatus
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from log_generator import log_function

logging = log_function("MCP")

# Import the database connection and execution logic from agents
logging.info("Importing DataBase Connection")
from agents.query_executor import get_db_connection, execute_query
from db_loader import load_csv_to_sqlite
from config import CSV_PATH, TABLE_NAME, DB_PATH

logging.info("DataBase Initialized")
# Ensure the database is initialized on server startup
print(f"Initializing database at {DB_PATH}...")
conn_init, _ = load_csv_to_sqlite(CSV_PATH, TABLE_NAME, DB_PATH)
if conn_init:
    conn_init.close()  # Close initial connection once DB setup is complete
    print("Database initialization complete.")
else:
    # If CSV or DB file is missing or malformed
    print(
        "WARNING: Database could not be initialized. \
        The server might not function correctly without data."
    )

logging.info("Creating FastAPI app instance")
# Create FastAPI app instance
app = FastAPI(
    title="Gen BI MCP Server",
    description="Module Context Protocol server for executing validated SQL queries.",
)


class SQLQueryRequest(BaseModel):
    """Request model for executing SQL queries."""

    sql_query: str


class ToolInfo(BaseModel):
    """Model for tool discovery information."""

    name: str
    description: str
    parameters: Dict[str, Any]


@app.get("/tools", response_model=List[ToolInfo], summary="Discover available tools")
async def get_tools():
    """
    Returns a list of available tools on the server, mimicking tool discovery in MCP.
    Provides tool metadata including required parameters and descriptions.
    """

    tools = [
        ToolInfo(
            name="execute_select_sql_query",
            description="Executes a validated SELECT SQL query on the connected SQLite database.",
            parameters={
                "type": "object",
                "properties": {
                    "sql_query": {
                        "type": "string",
                        "description": "The SQL SELECT query to execute.",
                    }
                },
                "required": ["sql_query"],
            },
        )
    ]
    return tools


@app.post("/execute_select_sql_query", summary="Execute a SELECT SQL query")
async def execute_select_sql_query(request: SQLQueryRequest):
    """
    Executes a given SQL query on the SQLite database, but only if it's a SELECT query.
    Validates query type, executes it, and returns results as JSON.
    """

    query = request.sql_query.strip()

    # Validate if it's a SELECT query (case-insensitive, ignores leading whitespace)
    if not re.match(r"^\s*SELECT", query, re.IGNORECASE):
        logging.error(
            f"SQLite {HTTPStatus.BAD_REQUEST}/case-insensitive, ignores leading whitespace"
        )
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail="Only SELECT queries are allowed for execution via this tool.",
        )

    conn = None
    try:
        # get_db_connection will attempt to connect to the DB_PATH
        conn = get_db_connection()
        results, col_names = execute_query(conn, query)

        # Convert sqlite3.Row objects to dictionaries for JSON serialization
        formatted_results = [dict(row) for row in results]

        return {"status": "success", "data": formatted_results, "columns": col_names}

    # Handle SQLite-related issues (e.g., invalid query, file not found)
    except sqlite3.Error as e:
        logging.error(
            f"SQLite {HTTPStatus.INTERNAL_SERVER_ERROR}/invalid query, file not found"
        )
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail=f"Database error: {e}. \
                    Ensure the database file '{DB_PATH}' exists and is accessible.",
        ) from e

    # Handle any unexpected errors during execution
    except Exception as e:
        logging.error(f"SQLite {HTTPStatus.INTERNAL_SERVER_ERROR}")
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {e}",
        ) from e

    # Always close the DB connection after use
    finally:
        if conn:
            conn.close()


# Entry point when script is run directly
if __name__ == "__main__":
    print("Starting MCP FastAPI server...")
    uvicorn.run(app, host="127.0.0.1", port=8000)
