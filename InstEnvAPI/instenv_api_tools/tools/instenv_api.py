from kubiya_sdk.tools.registry import tool_registry
from kubiya_sdk.tools.models import FileSpec, Arg
from pathlib import Path
from .base import InstEnvTool

# Get script contents
SCRIPT_DIR = Path(__file__).parent.parent / 'scripts'
with open(SCRIPT_DIR / 'api_client.py') as f:
    API_CLIENT_CODE = f.read()

def create_failure_analysis_tool():
    """Create a tool to analyze environment failure logs."""
    args = [
        Arg(name="environment_id", 
            description="Environment ID", 
            type="str",
            required=True)
    ]

    # Define required environment variables
    env = [
        "OPENAI_API_BASE",      # API base for OpenAI
        "SLACK_CHANNEL_ID",     # Slack channel ID
        "SLACK_THREAD_TS"       # Slack thread timestamp (optional)
    ]

    # Define secrets
    secrets = [
        "INSTENV_API_KEY",      # API key for InstEnv
        "OPENAI_API_KEY",       # API key for OpenAI
        "SLACK_API_TOKEN",      # API token for Slack
    ]

    file_specs = [
        FileSpec(destination="/opt/scripts/api_client.py", content=API_CLIENT_CODE),
        FileSpec(destination="/opt/scripts/utils/slack_messages.py", 
                content=open(SCRIPT_DIR / 'utils' / 'slack_messages.py').read()),
        FileSpec(destination="/opt/scripts/utils/log_analyzer.py",
                content=open(SCRIPT_DIR / 'utils' / 'log_analyzer.py').read()),
    ]

    mermaid_diagram = """
    sequenceDiagram
        participant U as 🧑 User
        participant T as 🛠️ Tool
        participant A as 🔌 InstEnv API
        participant O as 🤖 OpenAI
        participant S as 💬 Slack

        U->>+T: Request Failure Analysis
        T->>+A: Get Environment Info
        A-->>-T: Environment Data
        T->>+A: Get Failed Run Logs
        A-->>-T: Failure Logs
        T->>+O: Analyze Logs
        O-->>-T: Analysis Results
        T->>+S: Send Analysis Report
        S-->>-T: Notification Sent
        T-->>-U: Analysis Complete
    """

    return InstEnvTool(
        name="analyze_env_failure_logs",
        description="Analyzes environment failure logs and provides suggestions to fix issues",
        args=args,
        env=env,
        secrets=secrets,  # Add secrets definition
        content="""#!/bin/bash
set -e
echo ">> Processing request... ⏳"

# Install dependencies
pip install -q requests openai slack_sdk litellm pydantic

# Create python package structure
mkdir -p /opt/scripts/utils
touch /opt/scripts/__init__.py
touch /opt/scripts/utils/__init__.py

# Run the script
python /opt/scripts/api_client.py --env_id {{.environment_id}}
""",
        with_files=file_specs,
        mermaid=mermaid_diagram,
        image="python:3.11"
    )

# Create and register tools
try:
    tool = create_failure_analysis_tool()
    tool_registry.register("instenv_api", tool)
except Exception as e:
    print(f"Error creating tools: {e}")
    raise 