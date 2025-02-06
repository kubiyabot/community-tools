from kubiya_sdk.tools import Arg
from .base import KubiyaCliBase

# List Sources Tool
list_sources = KubiyaCliBase(
    name="list_sources",
    description="List all sources",
    cli_command='''
echo "📋 Listing sources..."

kubiya source list \\
    $([ -n "${output}" ] && echo "--output ${output}")
''',
    args=[
        Arg(name="output", type="str", description="Output format (json)", required=False),
    ],
)

# Scan Source Tool
scan_source = KubiyaCliBase(
    name="scan_source",
    description="Scan a source from URL or path",
    cli_command='''
echo "🔍 Scanning source..."

kubiya source scan "${url}" \\
    $([ "${local}" == "true" ] && echo "--local") \\
    $([ -n "${config}" ] && echo "--config ${config}")
''',
    args=[
        Arg(name="url", type="str", description="URL or path of the source to scan", required=True),
        Arg(name="local", type="str", description="Whether to scan local path", required=False, default="false"),
        Arg(name="config", type="str", description="Path to config file", required=False),
    ],
)

# Add Source Tool
add_source = KubiyaCliBase(
    name="add_source",
    description="Add a new source to Kubiya",
    cli_command='''
echo "➕ Adding source..."

kubiya source add "${url}" \\
    $([ -n "${name}" ] && echo "--name '${name}'") \\
    $([ -n "${config}" ] && echo "--config ${config}")
''',
    args=[
        Arg(name="url", type="str", description="URL of the source to add", required=True),
        Arg(name="name", type="str", description="Name of the source", required=False),
        Arg(name="config", type="str", description="Path to config file", required=False),
    ],
)

# Sync Source Tool
sync_source = KubiyaCliBase(
    name="sync_source",
    description="Sync an existing source in Kubiya",
    cli_command='''
echo "🔄 Syncing source..."

kubiya source sync "${uuid}" \\
    $([ -n "${mode}" ] && echo "--mode ${mode}") \\
    $([ -n "${branch}" ] && echo "--branch ${branch}") \\
    $([ "${force}" == "true" ] && echo "--force")
''',
    args=[
        Arg(name="uuid", type="str", description="UUID of the source to sync", required=True),
        Arg(name="mode", type="str", description="Sync mode (e.g., ci)", required=False),
        Arg(name="branch", type="str", description="Branch to sync from", required=False),
        Arg(name="force", type="str", description="Force sync", required=False, default="false"),
    ],
)

# Describe Source Tool
describe_source = KubiyaCliBase(
    name="describe_source",
    description="Describe a source",
    cli_command='''
echo "📝 Describing source..."

kubiya source describe "${uuid}" \\
    $([ -n "${output}" ] && echo "--output ${output}")
''',
    args=[
        Arg(name="uuid", type="str", description="UUID of the source to describe", required=True),
        Arg(name="output", type="str", description="Output format (json)", required=False),
    ],
)

# Delete Source Tool
delete_source = KubiyaCliBase(
    name="delete_source",
    description="Delete a source from Kubiya",
    cli_command='''
echo "🗑️ Deleting source..."

kubiya source delete "${uuid}" \\
    $([ "${force}" == "true" ] && echo "--force")
''',
    args=[
        Arg(name="uuid", type="str", description="UUID of the source to delete", required=True),
        Arg(name="force", type="str", description="Force deletion", required=False, default="false"),
    ],
)

# Register all tools
for tool in [list_sources, scan_source, add_source, sync_source, describe_source, delete_source]:
    KubiyaCliBase.register(tool)

__all__ = [
    'list_sources',
    'scan_source',
    'add_source',
    'sync_source',
    'describe_source',
    'delete_source',
] 