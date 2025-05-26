import inspect
import sys
from pathlib import Path
import json
import os

# Add the project root to Python path
project_root = str(Path(__file__).resolve().parents[2])
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from kubiya_sdk.tools.models import Arg, FileSpec, Volume
from kubiya_sdk.tools.registry import tool_registry
from kubiya_sdk.tools import Tool

SLACK_ICON_URL = "https://cdn-icons-png.flaticon.com/256/25/25231.png"

# Read the script content from the scripts directory
script_content = open(Path(__file__).parent.parent / 'scripts' / 'send_slack.py').read()

class SlackInvestigationTool(Tool):
    def __init__(
        self,
        name="slack_investigation",
        description="Send a notification that a PR failure is under investigation.",
        content="""
set -e
apk add --quiet py3-pip > /dev/null 2>&1
pip install slack-sdk fuzzywuzzy python-Levenshtein 2>&1 | grep -v '[notice]' > /dev/null

# Run the Python script
python /opt/scripts/send_slack.py "investigation" "{{ .pr_title }}" "{{ .pr_url }}"
""",
        args=[
            Arg(
                name="pr_title",
                description=(
                    "The title of the PR that failed.\n"
                    "*Example*: `Fix checkout validation`\n"
                    "*Format*: Plain text, no special formatting needed"
                ),
                required=True,
            ),
            Arg(
                name="pr_url",
                description=(
                    "The URL of the PR that failed.\n"
                    "*Example*: `https://github.com/org/repo/pull/123`\n"
                    "*Format*: Full GitHub PR URL"
                ),
                required=True,
            ),
        ],
        env=[
            "DESTINATION_CHANNEL",
        ],
        secrets=[
            "SLACK_API_TOKEN",
        ],
        with_files=[
            FileSpec(
                destination="/opt/scripts/send_slack.py",
                content=script_content,
            ),
        ],
        long_running=False,
    ):
        super().__init__(
            name=name,
            description=description,
            icon_url=SLACK_ICON_URL,
            type="docker",
            image="python:3.11-alpine",
            content=content,
            args=args,
            env=env,
            secrets=secrets,
            with_files=with_files,
            long_running=long_running,
        )

class SlackWorkflowSummaryTool(Tool):
    def __init__(
        self,
        name="slack_workflow_summary",
        description="""Send a failure summary message to Slack with PR details, failure information, and error details. The message includes PR title, URL, author, branch, what failed, why it failed, how to fix it, error details, and a link to the stack trace.""",
        content="""
set -e
apk add --quiet py3-pip jq > /dev/null 2>&1
pip install slack-sdk fuzzywuzzy python-Levenshtein 2>&1 | grep -v '[notice]' > /dev/null

# Create JSON input with proper escaping
JSON_INPUT=$(jq -n \
  --arg pr_title "{{ .pr_title }}" \
  --arg pr_url "{{ .pr_url }}" \
  --arg author "{{ .author }}" \
  --arg branch "{{ .branch }}" \
  --arg what_failed "{{ .what_failed }}" \
  --arg why_failed "{{ .why_failed }}" \
  --arg how_to_fix "{{ .how_to_fix }}" \
  --arg error_details "{{ .error_details }}" \
  --arg stack_trace_url "{{ .stack_trace_url }}" \
  '{
    "pr_title": $pr_title,
    "pr_url": $pr_url,
    "author": $author,
    "branch": $branch,
    "what_failed": $what_failed,
    "why_failed": $why_failed,
    "how_to_fix": $how_to_fix,
    "error_details": $error_details,
    "stack_trace_url": $stack_trace_url
  }')

# Run the Python script with JSON input
python /opt/scripts/send_slack.py "$JSON_INPUT"
""",
        args=[
            Arg(
                name="pr_title",
                description=(
                    "The title of the PR that failed.\n"
                    "*Example*: `Fix checkout validation`\n"
                    "*Format*: Plain text, no special formatting needed"
                ),
                required=True,
            ),
            Arg(
                name="pr_url",
                description=(
                    "The URL of the PR that failed.\n"
                    "*Example*: `https://github.com/org/repo/pull/123`\n"
                    "*Format*: Full GitHub PR URL"
                ),
                required=True,
            ),
            Arg(
                name="author",
                description=(
                    "The author of the PR.\n"
                    "*Example*: `@dev_alice`\n"
                    "*Format*: GitHub username with @ prefix"
                ),
                required=True,
            ),
            Arg(
                name="branch",
                description=(
                    "The branch name where the failure occurred.\n"
                    "*Example*: `feature/payment-bug`\n"
                    "*Format*: Branch name as it appears in GitHub"
                ),
                required=True,
            ),
            Arg(
                name="what_failed",
                description=(
                    "A description of what failed in the workflow.\n"
                    "*Example*: Tried to access user.email, but user was undefined\n"
                    "*Format*: Plain text only - DO NOT use backticks or any formatting\n"
                    "*Important*: Send as raw text, the script will handle formatting"
                ),
                required=True,
            ),
            Arg(
                name="why_failed",
                description=(
                    "An explanation of why the failure occurred.\n"
                    "*Example*: The user object was undefined during test execution, likely due to a missing or incorrect mock setup\n"
                    "*Format*: Plain text only - DO NOT use backticks or any formatting\n"
                    "*Important*: Send as raw text, the script will handle formatting"
                ),
                required=True,
            ),
            Arg(
                name="how_to_fix",
                description=(
                    "Instructions on how to fix the failure.\n"
                    "*Example*: Check if user is correctly mocked before test run. Make sure the email property exists before accessing it\n"
                    "*Format*: Plain text only - DO NOT use backticks or any formatting\n"
                    "*Important*: Send as raw text, the script will handle formatting"
                ),
                required=True,
            ),
            Arg(
                name="error_details",
                description=(
                    "The error message to display.\n"
                    "*Example*: Error: undefined: dsadas\n"
                    "*Format*: Plain text only - DO NOT use backticks or any formatting\n"
                    "*Important*: Send as raw text, the script will handle formatting"
                ),
                required=True,
            ),
            Arg(
                name="stack_trace_url",
                description=(
                    "URL to the GitHub Actions run or CI/CD logs where the error occurred.\n"
                    "*Example*: `https://github.com/org/repo/actions/runs/1234567890`\n"
                    "*Format*: Full GitHub Actions run URL or CI/CD logs URL that shows the error details"
                ),
                required=True,
            ),
        ],
        env=[
            "DESTINATION_CHANNEL",
        ],
        secrets=[
            "SLACK_API_TOKEN",
        ],
        with_files=[
            FileSpec(
                destination="/opt/scripts/send_slack.py",
                content=script_content,
            ),
        ],
        long_running=False,
    ):
        super().__init__(
            name=name,
            description=description,
            icon_url=SLACK_ICON_URL,
            type="docker",
            image="python:3.11-alpine",
            content=content,
            args=args,
            env=env,
            secrets=secrets,
            with_files=with_files,
            long_running=long_running,
        )

# Create and register the tools
slack_investigation_tool = SlackInvestigationTool()
slack_workflow_summary_tool = SlackWorkflowSummaryTool()

tool_registry.register("slack_investigation", slack_investigation_tool)
tool_registry.register("slack_workflow_summary", slack_workflow_summary_tool)

# Export the tools
__all__ = ["slack_investigation_tool", "slack_workflow_summary_tool"]

# Make sure the tools are available at module level
globals()["slack_investigation_tool"] = slack_investigation_tool
globals()["slack_workflow_summary_tool"] = slack_workflow_summary_tool