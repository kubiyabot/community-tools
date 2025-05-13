#!/bin/sh
set -e

# Expected environment variables from Kubiya ServiceSpec
# GIT_REPO_URL: URL of the MCP server's git repository
# GIT_BRANCH_OR_TAG: Branch or tag to checkout (e.g., main, v1.0.0)
# SERVER_FILE_PATH: Relative path within the repo to the MCP server Python file (e.g., my_server.py)
# MCP_INSTANCE_NAME: Name of the FastMCP instance in the server file (e.g., mcp, app)
# SERVICE_PORT: Port to run the MCP server on (e.g., 8000)

# Validate required environment variables
if [ -z "$GIT_REPO_URL" ] || [ -z "$GIT_BRANCH_OR_TAG" ] || [ -z "$SERVER_FILE_PATH" ] || [ -z "$MCP_INSTANCE_NAME" ] || [ -z "$SERVICE_PORT" ]; then
  echo "Error: Missing one or more required environment variables: GIT_REPO_URL, GIT_BRANCH_OR_TAG, SERVER_FILE_PATH, MCP_INSTANCE_NAME, SERVICE_PORT" >&2
  exit 1
fi

REPO_DIR="/app/mcp_server_code"

# Clone the repository
echo "Cloning MCP server from $GIT_REPO_URL (branch/tag: $GIT_BRANCH_OR_TAG)..."
rm -rf "$REPO_DIR" # Clean up previous clone if any
git clone --depth 1 --branch "$GIT_BRANCH_OR_TAG" "$GIT_REPO_URL" "$REPO_DIR"

cd "$REPO_DIR"

# Check if specific requirements.txt exists in the cloned repo and install them
if [ -f "requirements.txt" ]; then
    echo "Found requirements.txt in the repository. Installing dependencies..."
    pip install --no-cache-dir -r requirements.txt
elif [ -f "pyproject.toml" ]; then
    echo "Found pyproject.toml in the repository. Installing dependencies with pip..."
    # This is a basic attempt; more robust poetry/pdm handling might be needed if servers use them extensively
    pip install --no-cache-dir "."
fi

SERVER_FULL_PATH="$REPO_DIR/$SERVER_FILE_PATH"

if [ ! -f "$SERVER_FULL_PATH" ]; then
    echo "Error: Server file not found at $SERVER_FULL_PATH" >&2
    exit 1
fi

echo "Starting FastMCP server $SERVER_FULL_PATH:$MCP_INSTANCE_NAME on port $SERVICE_PORT..."

# Run the FastMCP server using streamable-http transport
# The fastmcp CLI looks for instances named mcp, server, or app by default if not specified.
# We pass it explicitly for robustness.
exec fastmcp run "${SERVER_FILE_PATH}:${MCP_INSTANCE_NAME}" --transport streamable-http --host 0.0.0.0 --port "${SERVICE_PORT}" 