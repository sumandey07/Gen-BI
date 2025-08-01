import os
import re
import torch
import pandas as pd
import streamlit as st
from mcp_client import call_mcp_sql_executor
from config import DB_PATH, CSV_PATH, TABLE_NAME
from db_loader import load_csv_to_sqlite
from graph_plotting import plot_query_results, extract_conditions_from_sql

# -----------------------------  UI FUNCTIONS  -----------------------------


from log_generator import log_function

# Initialize logger for utils.py
logger = log_function("utils")

# Use logger to log messages
logger.info("Utils module initialized.")


def setup_page():
    """Set Streamlit page configs and env flags."""
    st.set_page_config(page_title="Gen BI", layout="centered")
    hide_streamlit_style = """
    <style>
    [data-testid="stToolbar"] {
        visibility: hidden;
        height: 0%;
        position: fixed;
    }
    </style>
    """
    st.markdown(hide_streamlit_style, unsafe_allow_html=True)
    os.environ["STREAMLIT_SERVER_ENABLE_FILE_WATCHER"] = "false"
    torch.classes.__path__ = []  # Avoid Torch class path issues


# def display_ui_and_get_input():
#     """Render input text area and return query + button state."""
#     st.title("Gen BI")
#     user_input = st.text_area(
#         "Enter your natural language query:",
#         placeholder="e.g. Get total testcases executed for test_suite sn2 and platform c-8kv?",
#     )
#     submit = st.button("Generate SQL & Run", type="primary")
#     return user_input, submit


def display_ui_and_get_input():
    """Render a stylish UI for user query input and return the input + submit button state."""
    st.markdown(
        """
        <style>
        .main-title {
            font-size: 2.5rem;
            font-weight: 700;
            text-align: center;
            color: #333333;
            margin-bottom: 2rem; 
        }
        .query-label {
            font-size: 1.1rem;
            margin-bottom: 0.5rem;
            color: #444444;
        }
        .custom-input textarea {
            border-radius: 12px;
            border: 1px solid #cccccc;
            padding: 1rem;
            font-size: 1rem;
            color: #333333;
            background-color: #f9f9f9;
        }
        .stButton>button {
            background-color: #ff4b4b;
            color: white;
            font-weight: bold;
            padding: 0.6rem 1.5rem;
            border: none;
            border-radius: 8px;
            margin-top: 1rem;
            transition: background-color 0.3s ease;
        }
        .stButton>button:hover {
            background-color: #e04343;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="main-title">Gen BI</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="query-label">Enter your natural language query:</div>',
        unsafe_allow_html=True,
    )

    with st.container():
        user_input = st.text_area(
            label="",
            placeholder="e.g. Get total testcases executed for test_suite sn2 and platform c-8kv?",
            key="user_query_input",
            label_visibility="collapsed",
            height=100,
        )

    submit = st.button("Generate SQL & Run", type="primary")

    return user_input, submit


# ---------------------------  DATA & SCHEMA UTILS  ---------------------------


def get_schema_hint():
    """Load CSV to SQLite, return comma-separated column names."""
    conn, df = load_csv_to_sqlite(CSV_PATH, TABLE_NAME, DB_PATH)
    if conn:
        conn.close()

    if df is not None and isinstance(df, pd.DataFrame):
        return ", ".join(df.columns)

    st.error(f"No data loaded from '{CSV_PATH}'. Ensure the CSV exists and has data.")
    st.stop()


# ---------------------------  SQL UTILS  ---------------------------


def detect_metric_column(df, col_names):
    """
    Heuristically determine which column is the metric (y-axis) for plotting.
    """
    # Priority 1: Known metric names
    for col in col_names:
        if col.lower() in [
            "testcases_executed",
            "testcases_passed",
            "count",
            "sum",
            "avg",
            "min",
            "max",
        ]:
            return col

    # Priority 2: First numeric column in DataFrame
    for i, col in enumerate(col_names):
        if df[col].apply(lambda x: isinstance(x, (int, float))).all():
            return col

    # Priority 3: Fallback to last column
    if col_names:
        return col_names[-1]

    return None  # If all else fails


def extract_command_from_code_block(text: str) -> str:
    """
    Extract SQL from code block (```sql ... ```) or SELECT pattern.
    """
    block = re.search(r"```(?:sql)?\s*([\s\S]*?)\s*```", text)
    if block:
        return block.group(1).strip()

    select = re.search(r"(SELECT[\s\S]+?);?$", text, flags=re.IGNORECASE)
    return select.group(1).strip() if select else ""


# ---------------------------Modifying SQL for Visualisation------------------


def modify_sql_for_visualization(sql_query: str) -> str:
    """
    Modifies the SELECT clause of an SQL query to include all columns ('SELECT *')
    for better visualization, while preserving the WHERE clause.
    """
    sql_query_lower = sql_query.lower()

    # Check if it's a SELECT query
    if not sql_query_lower.startswith("select"):
        logger.warning(
            f"SQL query does not start with SELECT, skipping modification: {sql_query}"
        )
        return sql_query

    # Find the position of 'FROM'
    from_index = sql_query_lower.find("from")
    if from_index == -1:
        logger.warning(
            f"SQL query has no FROM clause, skipping modification: {sql_query}"
        )
        return sql_query

    # Extract everything after 'FROM' (including 'FROM' and the table name, and WHERE clause)
    # This also handles cases with JOINs, GROUP BY, ORDER BY, etc., by keeping them intact
    rest_of_query = sql_query[from_index:]

    # Construct the new query with SELECT *
    modified_sql_query = f"SELECT * {rest_of_query}"
    logger.info(f"Modified SQL for visualization: {modified_sql_query}")
    return modified_sql_query


# -------------------------  SQL EXECUTION HANDLER  -------------------------


def _extract_metric_from_select(original_sql_query: str) -> str | None:
    """
    Extracts the column name from the SELECT clause of an SQL query.
    Handles simple SELECTs and common aggregate functions.
    Returns the extracted column name or None if not found/complex.
    """
    match = re.search(
        r"SELECT\s+(?:(SUM|COUNT|AVG|MIN|MAX)\s*\(\s*(\w+)\s*\)|(\w+))\s+FROM",
        original_sql_query,
        re.IGNORECASE,
    )
    if match:
        if match.group(2):  # Aggregate function (e.g., SUM(column))
            # Returns the column name inside the aggregate, e.g., 'testcases_passed'
            return match.group(2)
        elif match.group(3):  # Direct column selection (e.g., SELECT column)
            return match.group(3)
    return None


def extract_selected_columns(sql: str) -> list[str]:
    """
    Extracts column names from the SELECT clause of the SQL query.
    Handles simple expressions and aliases.
    """
    match = re.search(r"SELECT\s+(.*?)\s+FROM", sql, re.IGNORECASE | re.DOTALL)
    if not match:
        return []

    select_clause = match.group(1)
    if select_clause.strip() == "*":
        return []

    columns = []
    for part in select_clause.split(","):
        col = part.strip()
        if " as " in col.lower():
            col = col.split(" as ")[0].strip()
        func_match = re.match(r"(sum|count|avg|min|max)\((.*?)\)", col, re.IGNORECASE)
        if func_match:
            col = func_match.group(2).strip()
        columns.append(col)
    return columns


def handle_sql_query_execution(sql_query_for_mcp: str, original_sql_query: str):
    if not sql_query_for_mcp.lower().startswith("select"):
        st.error("Only SELECT queries are supported.")
        return

    try:
        mcp_result_full = call_mcp_sql_executor(sql_query_for_mcp)
        mcp_result_user = call_mcp_sql_executor(original_sql_query)

        if (
            mcp_result_user.get("status") == "success"
            and mcp_result_user.get("data")
            and mcp_result_full.get("status") == "success"
            and mcp_result_full.get("data")
        ):
            df_user = pd.DataFrame(
                mcp_result_user["data"], columns=mcp_result_user["columns"]
            )
            df_full = pd.DataFrame(
                mcp_result_full["data"], columns=mcp_result_full["columns"]
            )

            context_cols = ["test_suite", "platform", "version"]
            for col in context_cols:
                if col in df_full.columns and col not in df_user.columns:
                    df_user[col] = df_full[col]

            ordered_cols = [col for col in context_cols if col in df_user.columns] + [
                col for col in df_user.columns if col not in context_cols
            ]
            df_user = df_user[ordered_cols]

            # Store in session state instead of displaying here
            st.session_state.df_user = df_user
            st.session_state.df_full = df_full

            # Chart data setup
            full_data = mcp_result_full["data"]
            full_cols = mcp_result_full["columns"]
            metric_col = _extract_metric_from_select(original_sql_query)

            if not metric_col:
                from utils import detect_metric_column

                metric_col = detect_metric_column(
                    pd.DataFrame(full_data, columns=full_cols), full_cols
                )

            if metric_col and metric_col in full_cols:
                st.session_state.full_data = full_data
                st.session_state.full_cols = full_cols
                st.session_state.metric_col = metric_col
                st.session_state.conditions = extract_conditions_from_sql(
                    sql_query_for_mcp
                )
            else:
                st.warning("Could not identify column for plotting.")
        else:
            st.warning("Query returned no results.")

    except Exception as e:
        st.error(f"Error: {e}")


def show_chart_from_cache():
    if not all(
        key in st.session_state for key in ["full_data", "full_cols", "metric_col"]
    ):
        return

    full_data = st.session_state.full_data
    full_cols = st.session_state.full_cols
    metric_col = st.session_state.metric_col
    conditions = st.session_state.get("conditions", [])

    if not metric_col and full_cols:
        for i, col in enumerate(full_cols):
            if (
                full_data
                and len(full_data[0]) > i
                and isinstance(full_data[0][i], (int, float))
            ):
                metric_col = col
                break

    if not metric_col:
        st.warning("No metric column found for plotting.")
        return

    st.markdown("### Visualizations")

    show_charts = st.checkbox("Show Graph Options", value=True, key="toggle_charts")

    if not show_charts:
        return  # User opted out of charts

    # Ensure full_data is a list of dicts
    if isinstance(full_data[0], dict):
        x_candidates = [col for col in full_cols if col != metric_col]
        pie_possible = False
        if x_candidates:
            x_col = x_candidates[0]
            unique_vals = set(row.get(x_col) for row in full_data)
            pie_possible = len(unique_vals) >= 2
    else:
        pie_possible = False

    st.subheader("Choose Chart Types to Display")

    show_bar = st.checkbox("Bar Chart", value=True, key="bar_chart")
    show_point = st.checkbox("Scatter Chart", value=False, key="point_chart")
    show_line = st.checkbox(
        "Line Chart", value=False, key="line_chart", disabled=len(full_data) < 2
    )
    show_pie = st.checkbox(
        "Pie Chart", value=False, key="pie_chart", disabled=not pie_possible
    )

    if show_bar:
        st.markdown("#### Bar Chart")
        plot_query_results(
            full_data, full_cols, metric_col, conditions, chart_type="Bar"
        )

    if show_point:
        st.markdown("#### Scatter Chart")
        plot_query_results(
            full_data, full_cols, metric_col, conditions, chart_type="Scatter"
        )

    if show_line:
        st.markdown("#### Line Chart")
        plot_query_results(
            full_data, full_cols, metric_col, conditions, chart_type="Line"
        )

    if show_pie:
        st.markdown("#### Pie Chart")
        plot_query_results(
            full_data, full_cols, metric_col, conditions, chart_type="Pie"
        )

    if not any([show_bar, show_point, show_line, show_pie]):
        st.info("Select at least one chart type to display.")
