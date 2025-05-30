from pathlib import Path

# Read the alert script content directly from file
scripts_dir = Path(__file__).resolve().parents[1] / "scripts"
with open(scripts_dir / "alert.py", "r") as f:
    alert_script_content = f.read()

from kubiya_sdk.tools.models import Arg, FileSpec
from kubiya_sdk.tools.registry import tool_registry

from .base import KubernetesPythonTool

# Define the Kubernetes alert tool
k8s_alert_tool = KubernetesPythonTool(
    name="k8s_alert",
    description=(
        "Send Kubernetes alert notifications to Slack with approval buttons.\n"
        "This tool sends alerts to a Slack channel with buttons for users to approve or deny proposed actions."
    ),
    content="""
    set -e
    python -m venv /opt/venv > /dev/null
    . /opt/venv/bin/activate > /dev/null
    pip install requests==2.32.3 2>&1 | grep -v '[notice]'

    # Run the alert script
    python /opt/scripts/alert.py "{{ .channel }}" "{{ .alert_title }}" "{{ .alert_message }}" "{{ .proposed_action }}"
    """,
    args=[
        Arg(
            name="channel",
            description="Slack channel to send the alert to (e.g., '#alerts' or 'C1234567890')",
            required=True,
        ),
        Arg(
            name="alert_title",
            description="Title of the Kubernetes alert (e.g., 'Pod CrashLooping')",
            required=True,
        ),
        Arg(
            name="alert_message",
            description="Detailed message describing the alert (e.g., 'Pod nginx-deployment-xyz is in CrashLoopBackOff state')",
            required=True,
        ),
        Arg(
            name="proposed_action",
            description="The action the AI wants to take (e.g., 'Restart the nginx-deployment')",
            required=True,
        ),
    ],
    env=[
        "KUBIYA_AGENT_UUID",
    ],
    secrets=[
        "SLACK_API_TOKEN",
    ],
    with_files=[
        FileSpec(
            destination="/opt/scripts/alert.py",
            content=alert_script_content,
        ),
    ],
    long_running=False,
    mermaid="""
    sequenceDiagram
        participant A as AI Agent
        participant S as System
        participant Slack as Slack Channel
        participant U as Users

        A ->> S: Detect K8s Alert
        S ->> Slack: Send Alert with Actions
        Slack -->> U: Display Alert & Buttons
        U ->> A: Approve/Deny Action
        A ->> S: Execute Approved Action
    """,
)


tool_registry.register("kubernetes", k8s_alert_tool)