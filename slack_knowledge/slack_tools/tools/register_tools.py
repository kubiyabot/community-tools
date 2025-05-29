import inspect
from kubiya_sdk import tool_registry
from kubiya_sdk.tools.models import Tool, FileSpec

from .knowledge import slack_knowledge

slack_knowledge_tool = Tool(
    name="slack_knowledge",
    description="answers questions based on the slack channel history",
    content="""
python /tmp/main.py
""",
    type="docker",
    image="python:3.12-slim",
    env=[
        "LLM_BASE_URL",
        "SLACK_DOMAIN",
        "KUBIYA_USER_ORG",
        "SLACK_THREAD_TS",
        "SLACK_CHANNEL_ID",
        "KUBIYA_USER_EMAIL",
        "KUBIYA_USER_MESSAGE",
    ],
    secrets=[
        "LLM_API_KEY",
        "KUBIYA_API_KEY",
        "SLACK_API_TOKEN",
    ],
    with_files=[
        FileSpec(
            destination="/tmp/main.py",
            content=inspect.getsource(slack_knowledge),
        )
    ],
)

tool_registry.register_tool("slack_knowledge", slack_knowledge_tool)
