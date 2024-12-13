from kubiya_sdk.tools import Arg
from .base import create_tool

# List Teammates Tool
teammate_list = create_tool(
    name="teammate_list",
    description="List all available virtual teammates and their capabilities",
    cli_command='''
echo "📋 Listing teammates..."

kubiya teammate list \\
    --output ${format} \\
    $([ -n "${filter}" ] && echo "--filter ${filter}") \\
    $([ -n "${sort}" ] && echo "--sort ${sort}") \\
    $([ -n "${limit}" ] && echo "--limit ${limit}")
''',
    args=[
        Arg(name="format", type="str", description="Output format (json|text)", required=False, default="json"),
        Arg(name="filter", type="str", description="Filter by expertise or domain", required=False),
        Arg(name="sort", type="str", description="Sort by (name|created|active)", required=False),
        Arg(name="limit", type="str", description="Max number of results", required=False),
    ],
)

# Get Teammate Details Tool
teammate_get = create_tool(
    name="teammate_get",
    description="Get detailed information about a virtual teammate's capabilities and expertise",
    cli_command='''
echo "🔍 Getting teammate details..."

kubiya teammate get \\
    $([ -n "${id}" ] && echo "--id ${id}") \\
    $([ -n "${name}" ] && echo "--name ${name}") \\
    --output ${format}
''',
    args=[
        Arg(name="id", type="str", description="Virtual teammate ID", required=False),
        Arg(name="name", type="str", description="Virtual teammate name", required=False),
        Arg(name="format", type="str", description="Output format (json|text)", required=False, default="json"),
    ],
)

# Search Teammates Tool
teammate_search = create_tool(
    name="teammate_search",
    description="Find virtual teammates based on their expertise and capabilities",
    cli_command='''
echo "🔎 Searching teammates..."

kubiya teammate search \\
    --query "${query}" \\
    $([ -n "${capability}" ] && echo "--capability ${capability}") \\
    $([ -n "${expertise}" ] && echo "--expertise ${expertise}") \\
    $([ -n "${limit}" ] && echo "--limit ${limit}") \\
    --output ${format}
''',
    args=[
        Arg(name="query", type="str", description="Search for specific skills or domains", required=True),
        Arg(name="capability", type="str", description="Filter by technical capability", required=False),
        Arg(name="expertise", type="str", description="Filter by expertise domain", required=False),
        Arg(name="limit", type="str", description="Max results to return", required=False, default="10"),
        Arg(name="format", type="str", description="Output format (json|text)", required=False, default="json"),
    ],
)

# List Teammate Capabilities Tool
teammate_capabilities = create_tool(
    name="teammate_capabilities",
    description="List all available capabilities and domains of expertise for virtual teammates",
    cli_command='''
echo "📋 Listing capabilities..."

kubiya teammate capabilities \\
    --output ${format} \\
    $([ -n "${category}" ] && echo "--category ${category}")
''',
    args=[
        Arg(name="format", type="str", description="Output format (json|text)", required=False, default="json"),
        Arg(name="category", type="str", description="Filter by capability domain", required=False),
    ],
)

__all__ = [
    'teammate_list',
    'teammate_get',
    'teammate_search',
    'teammate_capabilities',
] 