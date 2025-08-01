import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# You'll need to create this file with the provided schema
CSV_PATH = "raw_data_poc.csv"  # CSV File Path, as don't have actual db-server
TABLE_NAME = "test_results"
# FIXME: Used low-end model due to lack of infra, need to be replaced with higher-end model
MODEL_NAME = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
# MODEL_NAME = "google/flan-t5-base"
# MODEL_NAME = "mrm8488/t5-base-finetuned-wikiSQL"
# MODEL_NAME = "microsoft/phi-2"
# MODEL_NAME = "Qwen/Qwen2.5-3B"
DB_PATH = "test_results.db"  # Changed to a file-based database
REQUEST_TIMEOUT = 10  # Timeout for requests to the MCP server


# Attempt to get the MCP server URL
try:
    MCP_SERVER_URL = os.getenv("MCP_SERVER_URL")
    if not MCP_SERVER_URL:
        raise ValueError("MCP_SERVER_URL not found in environment.")
except ValueError as e:
    print(f"{e} Please enter the server URL manually:")
    MCP_SERVER_URL = input("Enter MCP_SERVER_URL: ")

# Attempt to get MCP_EXECUTE_TOOL_ENDPOINT
try:
    MCP_EXECUTE_TOOL_ENDPOINT = os.getenv("MCP_EXECUTE_TOOL_ENDPOINT")
    if not MCP_EXECUTE_TOOL_ENDPOINT:
        raise ValueError("MCP_EXECUTE_TOOL_ENDPOINT not found in environment.")
except ValueError as e:
    # Prompt the user to manually enter the endpoint if not found in .env
    print(f"{e} Please enter the server ENDPOINT manually:")
    MCP_EXECUTE_TOOL_ENDPOINT = input("Enter MCP_EXECUTE_TOOL_ENDPOINT manually: ")
