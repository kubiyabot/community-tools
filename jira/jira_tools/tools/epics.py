from ..base import JiraTool, register_jira_tool
from kubiya_sdk.tools import Arg

epic_list = JiraTool(
    name="epic_list",
    description="List Jira epics",
    content="""
    jira epic list $([[ "$table" == "true" ]] && echo "--table") \
                   $([[ -n "$reporter" ]] && echo "-r$reporter") \
                   $([[ -n "$status" ]] && echo "-s$status") \
                   $([[ -n "$assignee" ]] && echo "-a$assignee") \
                   $([[ -n "$priority" ]] && echo "-y$priority") \
                   $([[ -n "$order_by" ]] && echo "--order-by $order_by") \
                   $([[ "$reverse" == "true" ]] && echo "--reverse")
    """,
    args=[
        Arg(
            name="table",
            type="bool",
            description="Display in table view",
            required=False,
        ),
        Arg(
            name="reporter",
            type="str",
            description="Filter by reporter",
            required=False,
        ),
        Arg(name="status", type="str", description="Filter by status", required=False),
        Arg(
            name="assignee",
            type="str",
            description="Filter by assignee",
            required=False,
        ),
        Arg(
            name="priority",
            type="str",
            description="Filter by priority",
            required=False,
        ),
        Arg(
            name="order_by",
            type="str",
            description="Order results by field",
            required=False,
        ),
        Arg(
            name="reverse",
            type="bool",
            description="Reverse the order of results",
            required=False,
        ),
    ],
)

epic_create = JiraTool(
    name="epic_create",
    description="Create a new Jira epic",
    content="""
    jira epic create -n"$name" -s"$summary" -y"$priority" -p"$project_key" $([[ -n "$labels" ]] && echo "$labels") \
                     $([[ -n "$components" ]] && echo "$components") -b"$description" \
                     $([[ "$no_input" == "true" ]] && echo "--no-input") 
    """,
    args=[
        Arg(name="name", type="str", description="Epic name", required=True),
        Arg(name="summary", type="str", description="Epic summary", required=True),
        Arg(name="priority", type="str", description="Epic priority", required=True),
        Arg(name="labels", type="str", description="Epic labels", required=False),
        Arg(
            name="components", type="str", description="Epic components", required=False
        ),
        Arg(
            name="description",
            type="str",
            description="Epic description",
            required=True,
        ),
        Arg(
            name="no_input",
            type="bool",
            description="Skip interactive prompt",
            required=False,
        ),
        Arg(
            name="project_key",
            type="str",
            description="Jira project key",
            required=True,
        ),
    ],
)

epic_add = JiraTool(
    name="epic_add",
    description="Add issues to a Jira epic",
    content="jira epic add $epic_key $issues",
    args=[
        Arg(name="epic_key", type="str", description="Epic key", required=True),
        Arg(
            name="issues",
            type="str",
            description="Space-separated list of issue keys",
            required=True,
        ),
    ],
)

epic_remove = JiraTool(
    name="epic_remove",
    description="Remove issues from a Jira epic",
    content="jira epic remove $issues",
    args=[
        Arg(
            name="issues",
            type="str",
            description="Space-separated list of issue keys",
            required=True,
        ),
    ],
)

for tool in [epic_list, epic_create, epic_add, epic_remove]:
    register_jira_tool(tool)
