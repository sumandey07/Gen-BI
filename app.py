import time
import logging
import streamlit as st
from log_generator import log_function
from utils import (
    setup_page,
    get_schema_hint,
    display_ui_and_get_input,
    extract_command_from_code_block,
    handle_sql_query_execution,
    modify_sql_for_visualization,
)
from agents.query_filter import is_relevant_query
from agents.intent_generator import extract_intent
from agents.prompt_builder import generate_sql_query
from chat_history import ChatHistory
from utils import show_chart_from_cache

logger = log_function("app")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = ChatHistory()


def main():
    setup_page()
    schema_hint = get_schema_hint()
    user_input, submit = display_ui_and_get_input()

    logger.info("Taking input from user")

    if submit:
        if not user_input.strip():
            st.warning("Please enter a query.")
        elif not is_relevant_query(user_input):
            st.error(
                "Query doesn't seem relevant. Try including terms like 'platform', 'testcase', or 'version'."
            )
        else:
            with st.spinner("Processing..."):
                start_time = time.time()
                chat_history = st.session_state.chat_history

                cached_sql = chat_history.get_sql_for_question(user_input)
                if cached_sql:
                    intent = extract_intent(user_input)
                    sql_query = cached_sql
                    st.session_state.intent = intent
                    st.session_state.sql_query = sql_query
                    st.session_state.from_cache = True
                    chat_history.add_question_answer(user_input, sql_query)
                else:
                    raw_sql = generate_sql_query(user_input, schema_hint)
                    sql_query = (
                        extract_command_from_code_block(raw_sql) or raw_sql.strip()
                    )
                    intent = extract_intent(user_input)
                    st.session_state.intent = intent
                    st.session_state.sql_query = sql_query
                    st.session_state.from_cache = False
                    chat_history.add_question_answer(user_input, sql_query)

                sql_query_for_mcp = modify_sql_for_visualization(sql_query)
                st.session_state.sql_query_for_mcp = sql_query_for_mcp

                handle_sql_query_execution(sql_query_for_mcp, sql_query)
                duration = time.time() - start_time
                st.session_state.duration = duration

    # Always display previously generated content in correct order
    if "sql_query" in st.session_state and "intent" in st.session_state:
        st.subheader("Detected Entities")
        st.info(st.session_state.intent)

        st.subheader("Extracted SQL")
        st.code(st.session_state.sql_query, language="sql")
        if st.session_state.get("from_cache"):
            st.info("Using cached SQL query from previous interaction.")

        if "duration" in st.session_state:
            st.info("Executing SQL queries via MCP Server…")
            st.caption(
                f"Generated and executed in {st.session_state.duration:.2f} seconds"
            )

        if "df_user" in st.session_state:
            st.success("Query Result (with context):")
            st.dataframe(st.session_state.df_user, use_container_width=True)

        if "df_full" in st.session_state:
            st.subheader("Source:")
            st.dataframe(st.session_state.df_full, use_container_width=True)

    show_chart_from_cache()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler()],
    )
    main()
