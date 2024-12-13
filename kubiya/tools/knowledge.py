from kubiya_sdk.tools import Arg
from .base import create_tool

# Knowledge List Tool
knowledge_list = create_tool(
    name="knowledge_list",
    description="List all knowledge items in your Kubiya knowledge base",
    cli_command='''
echo "📋 Fetching knowledge list..."
kubiya knowledge list --output ${output_format}
''',
    args=[
        Arg(
            name="output_format",
            type="str",
            description="Output format (json|text)",
            required=False,
            default="json"
        ),
    ],
)

# Knowledge Get Tool
knowledge_get = create_tool(
    name="knowledge_get",
    description="Get details of a specific knowledge item",
    cli_command='''
echo "🔍 Fetching knowledge item details..."
kubiya knowledge get ${uuid} --output ${output_format}
''',
    args=[
        Arg(name="uuid", type="str", description="UUID of the knowledge item", required=True),
        Arg(
            name="output_format",
            type="str",
            description="Output format (json|text)",
            required=False,
            default="json"
        ),
    ],
)

# Knowledge Create Tool
knowledge_create = create_tool(
    name="knowledge_create",
    description="Create a new knowledge item",
    cli_command='''
echo "📝 Creating new knowledge item..."

# Create content file from input
CONTENT_FILE=$(create_content_file "${content}")

# Execute create command
kubiya knowledge create \\
    --name "${name}" \\
    --desc "${description}" \\
    $([ -n "${labels}" ] && echo "--labels ${labels}") \\
    --content-file "$CONTENT_FILE" \\
    --output json
''',
    args=[
        Arg(name="name", type="str", description="Name of the knowledge item", required=True),
        Arg(name="description", type="str", description="Description of the knowledge item", required=True),
        Arg(name="labels", type="str", description="Comma-separated list of labels", required=False, default=""),
        Arg(name="content", type="str", description="Content of the knowledge item", required=True),
    ],
)

# Knowledge Update Tool
knowledge_update = create_tool(
    name="knowledge_update",
    description="Update an existing knowledge item",
    cli_command='''
echo "📝 Updating knowledge item..."

# Create content file if content is provided
if [ -n "${content}" ]; then
    CONTENT_FILE=$(create_content_file "${content}")
    CONTENT_ARG="--content-file $CONTENT_FILE"
fi

# Execute update command
kubiya knowledge update ${uuid} \\
    $([ -n "${name}" ] && echo "--name \\"${name}\\"") \\
    $([ -n "${description}" ] && echo "--desc \\"${description}\\"") \\
    $([ -n "${labels}" ] && echo "--labels ${labels}") \\
    $CONTENT_ARG \\
    --yes \\
    --output json
''',
    args=[
        Arg(name="uuid", type="str", description="UUID of the knowledge item to update", required=True),
        Arg(name="name", type="str", description="New name for the knowledge item", required=False),
        Arg(name="description", type="str", description="New description for the knowledge item", required=False),
        Arg(name="labels", type="str", description="New comma-separated list of labels", required=False),
        Arg(name="content", type="str", description="New content for the knowledge item", required=False),
    ],
)

# Knowledge Delete Tool
knowledge_delete = create_tool(
    name="knowledge_delete",
    description="Delete a knowledge item",
    cli_command='''
echo "🗑️ Deleting knowledge item..."
kubiya knowledge delete ${uuid} --output json
''',
    args=[
        Arg(name="uuid", type="str", description="UUID of the knowledge item to delete", required=True),
    ],
)

# Knowledge Update Content Tool
knowledge_update_content = create_tool(
    name="knowledge_update_content",
    description="Update only the content of a knowledge item",
    cli_command='''
echo "📝 Updating knowledge item content..."

# Create content file from input
CONTENT_FILE=$(create_content_file "${content}")

# Execute update command with only content
kubiya knowledge update ${uuid} \\
    --content-file "$CONTENT_FILE" \\
    --yes \\
    --output json
''',
    args=[
        Arg(name="uuid", type="str", description="UUID of the knowledge item to update", required=True),
        Arg(name="content", type="str", description="New content for the knowledge item", required=True),
    ],
)

__all__ = [
    'knowledge_list',
    'knowledge_get',
    'knowledge_create',
    'knowledge_update',
    'knowledge_delete',
    'knowledge_update_content',
] 