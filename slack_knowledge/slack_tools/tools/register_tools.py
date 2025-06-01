import inspect
from kubiya_sdk import tool_registry
from kubiya_sdk.tools.models import Tool, FileSpec

from . import knowledge

slack_knowledge_tool = Tool(
    name="slack_knowledge",
    description="answers questions based on the slack channel history",
    content="""
python /tmp/main.py
""",
    type="docker",
    image="python:3.12-slim",
    on_build="pip install litellm==1.71.1 requests==2.32.3 pydantic==2.11.5 slack-sdk==3.35.0",
    env=[
        "LLM_BASE_URL",
        "SLACK_DOMAIN",
        "KUBIYA_USER_ORG",
        "SLACK_THREAD_TS",
        "SLACK_CHANNEL_ID",
        "KUBIYA_USER_EMAIL",
        "KUBIYA_USER_MESSAGE",
        "FIXED_SLACK_CHANNEL_ID",
        "FIXED_KUBIYA_API_KEY"
    ],
    secrets=[
        "LLM_API_KEY",
        "KUBIYA_API_KEY",
        "SLACK_API_TOKEN",
    ],
    with_files=[
        FileSpec(
            destination="/tmp/main.py",
            content=inspect.getsource(knowledge),
        )
    ],
)

tool_registry.register_tool("slack_knowledge", slack_knowledge_tool)
