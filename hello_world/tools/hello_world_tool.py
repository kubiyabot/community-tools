from kubiya_workflow_sdk.tools.models import Tool, Arg
from kubiya_workflow_sdk.tools.registry import tool_registry

say_hello_tool = Tool(
    name="say_hello",
    type="docker",
    image="python:3.12-slim-bullseye",
    description="Prints hello with name",
    args=[Arg(name="name", description="name to say hello to", required=True)],
    env=[],
    secrets=[],
    content="""
python -c "print(f'Hello, {{ .name }}!')"
""",
)

tool_registry.register_tool("hello_world", say_hello_tool)