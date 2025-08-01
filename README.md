# N2SQL MCP Chatbot

## Quick Start

1) **Create a virtual environment:**

    ```sh
    uv venv
    ```

2) **Activate the virtual environment:**

- **On Windows:**

    ```powershell
    .venv\Scripts\Activate
    ```

- **On Linux:**

    ```sh
    source .venv/bin/activate
    ```

3) **Install dependencies:**

    ```sh
    uv pip install -r requirements.txt
    ```

## Running the Application

- To start the backend server with `Uvicorn`:

  ```sh
  uvicorn mcp_server:app --reload
  ```

- To launch the `Streamlit` app:

  ```sh
  streamlit run app.py --server.headless true
  ```
