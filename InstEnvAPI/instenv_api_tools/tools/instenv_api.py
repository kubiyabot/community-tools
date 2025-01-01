from kubiya_sdk.tools.registry import tool_registry
from kubiya_sdk.tools.models import Tool, FileSpec, Arg
from pathlib import Path

# Tool icon and constants
INSTENV_ICON = "https://www.appnovation.com/sites/default/files/2019-06/partnerlogo_Atlassian.svg"

# Script paths
SCRIPT_DIR = Path(__file__).parent.parent / 'scripts'

# Load script contents
def load_script(name: str) -> str:
    with open(SCRIPT_DIR / name) as f:
        return f.read()

# Load all required scripts
API_CLIENT = load_script('api_client.py')
SLACK_MESSAGES = load_script('utils/slack_messages.py')
LOG_ANALYZER = load_script('utils/log_analyzer.py')

def create_failure_analysis_tool():
    """Create a tool to analyze environment failure logs."""
    args = [
        Arg(name="environment_id", 
            description="Environment ID", 
            type="str",
            required=True)
    ]

    env = [
        "OPENAI_API_BASE",
        "SLACK_CHANNEL_ID",
        "INSTENV_API_BASE"  # Base URL for InstEnv API (e.g., https://dev.instenv-ui.internal.atlassian.com/api/v1)
    ]

    secrets = [
        "INSTENV_API_KEY",
        "OPENAI_API_KEY",
        "SLACK_API_TOKEN"  # Required for Slack notifications
    ]

    file_specs = [
        FileSpec(destination="/opt/scripts/api_client.py", content=API_CLIENT),
        FileSpec(destination="/opt/scripts/utils/slack_messages.py", content=SLACK_MESSAGES),
        FileSpec(destination="/opt/scripts/utils/log_analyzer.py", content=LOG_ANALYZER)
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

    return Tool(
        name="analyze_env_failure_logs",
        description="Analyzes environment failure logs and provides suggestions to fix issues",
        icon_url=INSTENV_ICON,
        type="docker",
        image="python:3.11",
        content="""#!/bin/bash
set -e
echo ">> Processing request... ⏳"

# Install dependencies
pip install -q requests openai slack_sdk litellm pydantic

touch /opt/scripts/__init__.py
touch /opt/scripts/utils/__init__.py

# Run the script
python /opt/scripts/api_client.py --env_id {{.environment_id}}
""",
        args=args,
        env=env,
        secrets=secrets,
        with_files=file_specs,
        mermaid=mermaid_diagram
    )

# Create and register tool
analyze_env_failure_logs = create_failure_analysis_tool()
tool_registry.register("instenv_api", analyze_env_failure_logs)

# Export only the tool instance
__all__ = ['analyze_env_failure_logs'] 