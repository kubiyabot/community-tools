from kubiya_sdk.tools import Arg
from .base import KubiyaCliBase

# Create Webhook Tool
create_webhook = KubiyaCliBase(
    name="create_webhook",
    description="Create a webhook event to trigger teammate actions",
    cli_command='''webhook create \\
    --name "${name}" \\
    --instructions "${instructions}" \\
    --source "${source}" \\
    --output json''',
    args=[
        Arg(name="name", type="str", description="Name of the webhook event", required=True),
        Arg(name="instructions", type="str", description="Instructions for the webhook event", required=True),
        Arg(name="source", type="str", description="Source description for the webhook event", required=True),
    ],
)

# List Webhooks Tool
list_webhooks = KubiyaCliBase(
    name="list_webhooks",
    description="List all webhooks",
    cli_command="webhook list",
    args=[],
)

# Get Webhook Tool
get_webhook = KubiyaCliBase(
    name="get_webhook",
    description="Get details of a specific webhook",
    cli_command="webhook get ${webhook_id}",
    args=[
        Arg(name="webhook_id", type="str", description="ID of the webhook to get", required=True),
    ],
)

# Delete Webhook Tool
delete_webhook = KubiyaCliBase(
    name="delete_webhook",
    description="Delete a webhook",
    cli_command="webhook delete ${webhook_id}",
    args=[
        Arg(name="webhook_id", type="str", description="ID of the webhook to delete", required=True),
    ],
)

# Register all tools
for tool in [create_webhook, list_webhooks, get_webhook, delete_webhook]:
    KubiyaCliBase.register(tool)

__all__ = [
    'create_webhook',
    'list_webhooks',
    'get_webhook',
    'delete_webhook',
]