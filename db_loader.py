# db_loader.py

import os
import pandas as pd
import sqlite3
from config import TABLE_NAME, CSV_PATH, DB_PATH


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize column names: lowercase, strip whitespace, replace spaces with underscores.
    """
    df.columns = [col.strip().lower().replace(" ", "_") for col in df.columns]
    return df


def read_csv_safely(csv_path: str) -> pd.DataFrame | None:
    """
    Safely reads a CSV file, returning a DataFrame or None if failure occurs.
    """
    if not os.path.exists(csv_path):
        print(f"Error: CSV file '{csv_path}' not found.")
        return None

    try:
        df = pd.read_csv(csv_path)
        if df.empty:
            print(f"Warning: CSV file '{csv_path}' contains no data.")
            return None
        return df
    except pd.errors.EmptyDataError:
        print(f"Warning: CSV file '{csv_path}' is empty.")
    except Exception as e:
        print(f"Error reading CSV file '{csv_path}': {e}")
    return None


def write_df_to_sqlite(
    df: pd.DataFrame, db_path: str, table_name: str
) -> sqlite3.Connection | None:
    """
    Writes the DataFrame into the SQLite database and returns the connection.
    """
    try:
        conn = sqlite3.connect(db_path)
        df.to_sql(table_name, conn, index=False, if_exists="replace")
        print(
            f"Data loaded from CSV to SQLite database '{db_path}', table '{table_name}'."
        )
        return conn
    except sqlite3.Error as e:
        print(f"Error writing to SQLite database '{db_path}': {e}")
        if conn:
            conn.close()
    return None


def load_csv_to_sqlite(csv_path=CSV_PATH, table_name=TABLE_NAME, db_path=DB_PATH):
    """
    Loads data from a CSV into a SQLite DB.
    Returns (connection, dataframe) if successful, else (None, None).
    """
    df = read_csv_safely(csv_path)
    if df is None:
        return None, None

    df = normalize_columns(df)
    conn = write_df_to_sqlite(df, db_path, table_name)

    return (conn, df) if conn else (None, None)


# Script entry point for local testing
if __name__ == "__main__":
    conn, df = load_csv_to_sqlite()
    if conn and df is not None:
        print(f"Successfully loaded {len(df)} rows.")
        try:
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM {TABLE_NAME} LIMIT 5")
            print("Sample data:")
            for row in cursor.fetchall():
                print(row)
        except Exception as e:
            print(f"Error testing DB: {e}")
        finally:
            conn.close()
    else:
        print("Failed to load data or no data available.")
