# Use a Python base image
FROM python:3.11-slim

# Install git
RUN apt-get update && apt-get install -y git --no-install-recommends && rm -rf /var/lib/apt/lists/*

# Install FastMCP and its dependencies
# You might need to adjust this based on your specific MCP server's requirements
RUN pip install --no-cache-dir "fastmcp>=2.3.0" uvicorn httpx

# Create a working directory
WORKDIR /app

# Copy the entrypoint script and make it executable
COPY entrypoint.sh .
RUN chmod +x entrypoint.sh

# Expose the default MCP service port (can be overridden)
EXPOSE 8000

# Set the entrypoint
ENTRYPOINT ["/app/entrypoint.sh"] 