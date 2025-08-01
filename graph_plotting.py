import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import logging
import streamlit as st
import base64
import io
import uuid

logger = logging.getLogger(__name__)


def extract_conditions_from_sql(sql_query):
    where_index = sql_query.lower().find("where")
    if where_index != -1:
        conditions = sql_query[where_index + len("where") :].strip()
        logger.info(f"Extracted conditions: {conditions}")
        return conditions
    logger.warning("No conditions found in SQL query.")
    return "No conditions"


def _escape_js_template_literal(s):
    return str(s).replace("`", "\\`")


def plot_query_results(
    result_data, col_names, metric_col, conditions, chart_type="Bar"
):
    if not result_data:
        logger.warning("No data to plot.")
        st.warning("No data to plot.")
        return

    df = pd.DataFrame(result_data, columns=col_names)
    col_names_lower = [col.lower() for col in col_names]
    metric_col_lower = metric_col.lower()
    x_col = None
    conditions_lower = conditions.lower()

    # Determine x-axis column
    if "test_suite" in conditions_lower and "platform" in col_names_lower:
        x_col = col_names[col_names_lower.index("platform")]
    elif "platform" in conditions_lower and "test_suite" in col_names_lower:
        x_col = col_names[col_names_lower.index("test_suite")]
    elif "release_version" in conditions_lower and "platform" in col_names_lower:
        x_col = col_names[col_names_lower.index("platform")]

    if x_col is None:
        potential_x_cols = [col for col in col_names if col.lower() != metric_col_lower]
        potential_x_cols_lower = [col.lower() for col in potential_x_cols]
        for preferred in ["platform", "test_suite", "release_version"]:
            if preferred in potential_x_cols_lower:
                x_col = col_names[potential_x_cols_lower.index(preferred)]
                break
        if not x_col and potential_x_cols:
            x_col = potential_x_cols[0]
        if not x_col:
            if len(df) > 1:
                x_col = "__data_point_index__"
                df[x_col] = [f"Entry {i+1}" for i in range(len(df))]
            else:
                x_col = "__conditions_label__"
                df[x_col] = conditions or "Result"

    if x_col in df.columns:
        df[x_col] = df[x_col].astype(str)

    if x_col not in ["__data_point_index__", "__conditions_label__"] and len(df) > 1:
        if df[x_col].nunique() == 1:
            x_col = "__data_point_index__"
            df[x_col] = [f"Entry {i+1}" for i in range(len(df))]

    y_max = 0
    if metric_col in df.columns:
        y_max = df[metric_col].max()
    if "testcases_failed" in df.columns:
        y_max = max(y_max, df["testcases_failed"].max())
    y_axis_range = [0, y_max * 1.25]

    # Intent analysis
    intent = st.session_state.get("intent", "").lower()
    show_passed = "testcases passed" in intent and "testcases_passed" in df.columns
    show_executed = (
        "testcases executed" in intent and "testcases_executed" in df.columns
    )
    show_failed = "testcases_failed" in df.columns
    plot_pass_fail = (show_passed or show_executed) and show_failed

    fig = go.Figure()
    x_axis_title = x_col.replace("_", " ").capitalize()

    if chart_type == "Bar":
        if plot_pass_fail:
            if show_passed:
                fig.add_trace(
                    go.Bar(
                        x=df[x_col],
                        y=df["testcases_passed"],
                        name="Testcases Passed",
                        marker_color="#2ECC71",
                        text=df["testcases_passed"],
                        textposition="auto",
                        hovertemplate="%{x}<br>Testcases Passed: %{y}<extra></extra>",
                    )
                )
            if show_executed:
                fig.add_trace(
                    go.Bar(
                        x=df[x_col],
                        y=df["testcases_executed"],
                        name="Testcases Executed",
                        marker_color="#4C78A8",
                        text=df["testcases_executed"],
                        textposition="auto",
                        hovertemplate="%{x}<br>Testcases Executed: %{y}<extra></extra>",
                    )
                )
            fig.add_trace(
                go.Bar(
                    x=df[x_col],
                    y=df["testcases_failed"],
                    name="Testcases Failed",
                    marker_color="#E74C3C",
                    text=df["testcases_failed"],
                    textposition="auto",
                    hovertemplate="%{x}<br>Testcases Failed: %{y}<extra></extra>",
                )
            )
        else:
            fig.add_trace(
                go.Bar(
                    x=df[x_col],
                    y=df[metric_col],
                    name=metric_col,
                    marker_color="#4C78A8",
                    text=df[metric_col],
                    textposition="auto",
                    hovertemplate=f"%{{x}}<br>{metric_col}: %{{y}}<extra></extra>",
                )
            )

        fig.update_layout(
            template="plotly_white",
            xaxis_title=x_axis_title,
            yaxis_title="Count",
            bargap=0.3,
            yaxis_range=y_axis_range,
            margin=dict(l=100, r=100, t=100, b=100),
            hovermode="x unified",
        )

    elif chart_type == "Scatter":
        if plot_pass_fail:
            if show_passed:
                fig.add_trace(
                    go.Scatter(
                        x=df[x_col],
                        y=df["testcases_passed"],
                        mode="markers+text",
                        name="Testcases Passed",
                        marker=dict(color="#2ECC71", size=10),
                        text=df["testcases_passed"],
                        textposition="top center",
                        hovertemplate="%{x}<br>Testcases Passed: %{y}<extra></extra>",
                    )
                )
            if show_executed:
                fig.add_trace(
                    go.Scatter(
                        x=df[x_col],
                        y=df["testcases_executed"],
                        mode="markers+text",
                        name="Testcases Executed",
                        marker=dict(color="#4C78A8", size=10),
                        text=df["testcases_executed"],
                        textposition="top center",
                        hovertemplate="%{x}<br>Testcases Executed: %{y}<extra></extra>",
                    )
                )
            fig.add_trace(
                go.Scatter(
                    x=df[x_col],
                    y=df["testcases_failed"],
                    mode="markers+text",
                    name="Testcases Failed",
                    marker=dict(color="#E74C3C", size=10),
                    text=df["testcases_failed"],
                    textposition="top center",
                    hovertemplate="%{x}<br>Testcases Failed: %{y}<extra></extra>",
                )
            )
        else:
            fig = px.scatter(df, x=x_col, y=metric_col, text=metric_col)
            fig.update_traces(
                marker=dict(color="#F58518"),
                textposition="top center",
                hovertemplate=f"%{{x}}<br>{metric_col}: %{{y}}<extra></extra>",
            )

        fig.update_layout(
            template="plotly_white",
            xaxis_title=x_axis_title,
            yaxis_title="Count",
            yaxis_range=y_axis_range,
            margin=dict(l=100, r=100, t=100, b=100),
            hovermode="closest",
        )

    elif chart_type == "Line":
        if plot_pass_fail:
            if show_passed:
                fig.add_trace(
                    go.Scatter(
                        x=df[x_col],
                        y=df["testcases_passed"],
                        mode="lines+markers+text",
                        name="Testcases Passed",
                        line=dict(color="#2ECC71"),
                        text=df["testcases_passed"],
                        textposition="top center",
                        hovertemplate="%{x}<br>Testcases Passed: %{y}<extra></extra>",
                    )
                )
            if show_executed:
                fig.add_trace(
                    go.Scatter(
                        x=df[x_col],
                        y=df["testcases_executed"],
                        mode="lines+markers+text",
                        name="Testcases Executed",
                        line=dict(color="#4C78A8"),
                        text=df["testcases_executed"],
                        textposition="top center",
                        hovertemplate="%{x}<br>Testcases Executed: %{y}<extra></extra>",
                    )
                )
            fig.add_trace(
                go.Scatter(
                    x=df[x_col],
                    y=df["testcases_failed"],
                    mode="lines+markers+text",
                    name="Testcases Failed",
                    line=dict(color="#E74C3C"),
                    text=df["testcases_failed"],
                    textposition="top center",
                    hovertemplate="%{x}<br>Testcases Failed: %{y}<extra></extra>",
                )
            )
        else:
            fig = px.line(df, x=x_col, y=metric_col, markers=True, text=metric_col)
            fig.update_traces(
                line=dict(color="#72B7B2"),
                textposition="top center",
                hovertemplate=f"%{{x}}<br>{metric_col}: %{{y}}<extra></extra>",
            )

        fig.update_layout(
            template="plotly_white",
            xaxis_title=x_axis_title,
            yaxis_title="Count",
            yaxis_range=y_axis_range,
            margin=dict(l=100, r=100, t=100, b=100),
            hovermode="x unified",
        )

    elif chart_type == "Pie":
        fig = px.pie(df, names=x_col, values=metric_col, hole=0.3)
        fig.update_traces(textinfo="percent+label")

    else:
        st.warning(f"Chart type '{chart_type}' not supported.")
        st.dataframe(df, use_container_width=True)
        return

    chart_col, button_col = st.columns([0.9, 0.1])
    with chart_col:
        st.plotly_chart(fig, use_container_width=True)

    with button_col:
        img_buffer = io.BytesIO()
        try:
            fig.write_image(img_buffer, format="png")
            img_base64 = base64.b64encode(img_buffer.getvalue()).decode("utf-8")
            uid = f"copyButton_{uuid.uuid4().hex}"
            js_img_base64 = _escape_js_template_literal(img_base64)

            st.components.v1.html(
                f"""
                <div style="display: flex; justify-content: center; align-items: center; height: 75px;">
                    <button id="{uid}" style="
                        background: #ddd;
                        border: #bbb;
                        border-radius: 8px;
                        padding: 10px 10px;
                        cursor: pointer;
                        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                        transition: all 0.3s ease;
                        display: flex;
                        align-items: center;">
                        📋 Copy Chart
                    </button>
                </div>
                <script>
                    document.getElementById('{uid}').addEventListener('click', async () => {{
                        try {{
                            const byteCharacters = atob(`{js_img_base64}`);
                            const byteArray = new Uint8Array([...byteCharacters].map(c => c.charCodeAt(0)));
                            const blob = new Blob([byteArray], {{ type: 'image/png' }});
                            await navigator.clipboard.write([new ClipboardItem({{'image/png': blob}})]);
                            alert('Graph copied to clipboard!');
                        }} catch (e) {{
                            alert('Copy failed: ' + e.message);
                        }}
                    }});
                </script>
                """,
                height=90,
            )
        except Exception as e:
            logger.error(f"Graph image generation error: {e}")
            st.warning("Could not copy graph image.")
