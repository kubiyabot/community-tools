from kubiya_sdk.tools import Arg
from .base import KubiyaTool
from kubiya_sdk.tools.registry import tool_registry

# Kubiya Create Webhook Tool
kubiya_create_webhook = KubiyaTool(
    name="kubiya_create_webhook",
    description="Create a webhook event with the Kubiya API, webhook events are used to trigger team mates to perform actions based on third party events",
    action="create_webhook",
    args=[
        Arg(name="name", type="str", description="The name of the webhook event", required=True),
        Arg(name="ai_instructions", type="str", description="The AI instructions for the webhook event", required=True),
        Arg(name="source", type="str", description="The source of the webhook event - simple text description of why the webhook event is in the queue", required=True),
    ],
)

# Add more webhook-related tools here as needed

# Update the all_tools list
all_tools = [
    kubiya_create_webhook,
    # Add more tools here as they are created
]

# Register all Kubiya webhook tools
for tool in all_tools:
    tool_registry.register("kubiya_webhook", tool)