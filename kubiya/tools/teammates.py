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
    mermaid='''
graph TD
    A[List Teammates] --> B{Check Filters}
    B -->|No Filters| C[Get All Teammates]
    B -->|Has Filters| D[Apply Filters]
    D --> E{Filter Type}
    E -->|Domain| F[Filter by Domain]
    E -->|Expertise| G[Filter by Expertise]
    E -->|Active| H[Filter by Status]
    F --> I[Format Results]
    G --> I
    H --> I
    C --> I
    I -->|JSON| J[JSON Output]
    I -->|Text| K[Text Output]
    '''
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
    mermaid='''
graph TD
    A[Get Teammate] --> B{ID or Name?}
    B -->|ID| C[Lookup by ID]
    B -->|Name| D[Lookup by Name]
    C --> E[Get Teammate Details]
    D --> E
    E --> F{Fetch Info}
    F --> G[Basic Info]
    F --> H[Capabilities]
    F --> I[Expertise]
    F --> J[History]
    G --> K[Format Output]
    H --> K
    I --> K
    J --> K
    '''
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
    mermaid='''
graph TD
    A[Search Query] --> B[Parse Search Terms]
    B --> C{Search Type}
    C -->|Skills| D[Search Skills]
    C -->|Domain| E[Search Domain]
    C -->|Capability| F[Search Capabilities]
    D --> G[Apply Filters]
    E --> G
    F --> G
    G --> H[Sort Results]
    H --> I[Apply Limits]
    I --> J[Format Output]
    '''
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
    mermaid='''
graph TD
    A[List Capabilities] --> B{Has Category?}
    B -->|Yes| C[Filter by Category]
    B -->|No| D[Get All Capabilities]
    C --> E[Group Capabilities]
    D --> E
    E --> F[Technical Skills]
    E --> G[Domain Knowledge]
    E --> H[Integration Types]
    F --> I[Format Output]
    G --> I
    H --> I
    '''
)

__all__ = [
    'teammate_list',
    'teammate_get',
    'teammate_search',
    'teammate_capabilities',
] 