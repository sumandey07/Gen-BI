import sqlite3
from config import DB_PATH


def get_db_connection():
    """Returns a connection object to the SQLite database."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # This allows accessing columns by name
    return conn


def execute_query(connection, sql_query):
    """
    Executes an SQL query on the given SQLite connection.
    Returns the fetched results and column names.
    """
    cursor = connection.execute(sql_query)
    result = cursor.fetchall()
    col_names = [desc[0] for desc in cursor.description]
    return result, col_names
