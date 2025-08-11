import json
import requests
from config import MCP_SERVER_URL, MCP_EXECUTE_TOOL_ENDPOINT, REQUEST_TIMEOUT
import requests

def call_mcp_sql_executor(sql_query: str) -> dict:
    """
    Sends a SQL query to the MCP server and returns the response JSON.
    """
    try:
        response = requests.post(
            url="https://gen-bi-ppn3.onrender.com/execute_select_sql_query",
            json={"sql_query": sql_query},
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        return response.json()
        
    except requests.exceptions.ConnectionError as conn_err:
        _raise_connection_error("SQL execution", conn_err)

    except requests.exceptions.HTTPError as http_err:
        _raise_http_error("SQL execution", http_err)

    except json.JSONDecodeError as json_err:
        raise RuntimeError(
            f"Failed to decode JSON response from MCP Server during SQL execution: {json_err}."
        ) from json_err

    except Exception as e:
        raise RuntimeError(
            f"An unexpected error occurred during MCP SQL execution: {e}"
        ) from e


def discover_mcp_tools() -> list:
    """
    Retrieves available tools from the MCP server.
    """
    try:
        response = requests.get("https://gen-bi-ppn3.onrender.com/tools", timeout=REQUEST_TIMEOUT)
        response.raise_for_status()

        try:
            return response.json()
        except json.JSONDecodeError as json_err:
            raise RuntimeError(
                f"Failed to decode JSON response from MCP Server during tool discovery: "
                f"{json_err}. Response: {response.text}"
            ) from json_err

    except requests.exceptions.ConnectionError as conn_err:
        _raise_connection_error("tool discovery", conn_err)

    except requests.exceptions.HTTPError as http_err:
        _raise_http_error("tool discovery", http_err)

    except Exception as e:
        raise RuntimeError(
            f"An unexpected error occurred during MCP tool discovery: {e}"
        ) from e


# --- Private helper functions --- #


def _raise_connection_error(context: str, conn_err: Exception):
    raise requests.exceptions.ConnectionError(
        f"Could not connect to MCP Server at {MCP_SERVER_URL} during {context}. "
        "Please ensure 'mcp_server.py' is running."
    ) from conn_err


def _raise_http_error(context: str, http_err: Exception):
    try:
        error_detail = http_err.response.json().get("detail", str(http_err))
    except json.JSONDecodeError:
        error_detail = http_err.response.text
    raise requests.exceptions.HTTPError(
        f"Error from MCP Server during {context}: {error_detail}"
    ) from http_err
