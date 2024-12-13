from kubiya_sdk.tools import Arg
from .base import create_tool

# Create Webhook Tool
create_webhook = create_tool(
    name="create_webhook",
    description="Create a webhook event to trigger teammate actions",
    cli_command='''
echo "🔗 Creating webhook..."

kubiya webhook create \\
    --name "${name}" \\
    --instructions "${instructions}" \\
    --source "${source}" \\
    --output json
''',
    args=[
        Arg(name="name", type="str", description="Name of the webhook event", required=True),
        Arg(name="instructions", type="str", description="Instructions for the webhook event", required=True),
        Arg(name="source", type="str", description="Source description for the webhook event", required=True),
    ],
)

# List Webhooks Tool
list_webhooks = create_tool(
    name="list_webhooks",
    description="List all webhooks",
    cli_command='''
echo "📋 Listing webhooks..."

kubiya webhook list \\
    --output ${output_format} \\
    $([ -n "${filter}" ] && echo "--filter ${filter}")
''',
    args=[
        Arg(name="output_format", type="str", description="Output format (json|text)", required=False, default="json"),
        Arg(name="filter", type="str", description="Filter webhooks by name or source", required=False),
    ],
)

# Delete Webhook Tool
delete_webhook = create_tool(
    name="delete_webhook",
    description="Delete a webhook",
    cli_command='''
echo "🗑️ Deleting webhook..."

kubiya webhook delete \\
    --id "${webhook_id}" \\
    --output json
''',
    args=[
        Arg(name="webhook_id", type="str", description="ID of the webhook to delete", required=True),
    ],
)

__all__ = [
    'create_webhook',
    'list_webhooks',
    'delete_webhook',
]