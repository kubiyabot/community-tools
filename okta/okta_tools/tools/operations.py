from kubiya_sdk.tools import Arg
from .base import OktaTool
from kubiya_sdk.tools.registry import tool_registry

# User Operations
# Get User Tool with Field Selection
okta_get_user = OktaTool(
    name="get_user",
    description="Get user information by ID or email",
    action="users",
    args=[
        Arg(
            name="identifier",
            type="str",
            description="User ID or email address",
            required=True
        ),
        Arg(
            name="fields",
            type="str",
            description="Comma-separated list of fields to return (e.g., 'profile,status,lastLogin')",
            required=False
        ),
    ],
)

# Search Users Tool
okta_search_users = OktaTool(
    name="search_users",
    description="Search users with advanced query options",
    action="users",
    args=[
        Arg(
            name="query",
            type="str",
            description=(
                "SCIM filter (e.g., 'profile.firstName eq \"John\"' or "
                "'profile.lastName sw \"Smith\" and profile.email co \"@example.com\"')"
            ),
            required=False
        ),
        Arg(
            name="filter",
            type="str",
            description=(
                "Okta filter expression (e.g., 'status eq \"ACTIVE\" or "
                "lastUpdated gt \"2023-01-01T00:00:00.000Z\"')"
            ),
            required=False
        ),
        Arg(
            name="search",
            type="str",
            description="Free-form text search across most user fields",
            required=False
        ),
        Arg(
            name="limit",
            type="int",
            description="Maximum number of results (1-200)",
            required=False
        ),
        Arg(
            name="after",
            type="str",
            description="Pagination cursor for getting next page of results",
            required=False
        ),
    ],
)

# List Users Tool
okta_list_users = OktaTool(
    name="list_users",
    description="List all users in Okta",
    action="users",
    args=[
        Arg(
            name="limit",
            type="int",
            description="Maximum number of results per page (1-200)",
            required=False
        ),
        Arg(
            name="after",
            type="str",
            description="Pagination cursor for next page",
            required=False
        ),
    ],
)

# Group Operations
# List Groups Tool
okta_list_groups = OktaTool(
    name="list_groups",
    description="List all groups in Okta with optional filtering",
    action="groups",
    args=[
        Arg(name="query", type="str", description="Search query to filter groups", required=False),
        Arg(name="filter", type="str", description="Filter expression for groups", required=False),
        Arg(name="after", type="str", description="Pagination cursor", required=False),
        Arg(name="limit", type="int", description="Number of results (max 200)", required=False),
    ],
)

# Create Group Tool
okta_create_group = OktaTool(
    name="create_group",
    description="Create a new Okta group",
    action="groups",
    args=[
        Arg(name="name", type="str", description="Name of the group", required=True),
        Arg(name="description", type="str", description="Description of the group", required=False),
        Arg(name="skip_naming_conflict_resolution", type="bool", description="Skip name conflict checking", required=False),
    ],
)

# Update Group Tool
okta_update_group = OktaTool(
    name="update_group",
    description="Update an existing Okta group",
    action="groups",
    args=[
        Arg(name="group_id", type="str", description="ID of the group to update", required=True),
        Arg(name="name", type="str", description="New name for the group", required=True),
        Arg(name="description", type="str", description="New description for the group", required=False),
    ],
)

# Delete Group Tool
okta_delete_group = OktaTool(
    name="delete_group",
    description="Delete an Okta group",
    action="groups",
    args=[
        Arg(name="group_id", type="str", description="ID of the group to delete", required=True),
    ],
)

# Get Group Info Tool
okta_get_group = OktaTool(
    name="get_group",
    description="Get information about an Okta group",
    action="groups",
    args=[
        Arg(name="group_id", type="str", description="ID of the group", required=True),
    ],
)

# List Group Members Tool
okta_list_members = OktaTool(
    name="list_members",
    description="List all members of an Okta group",
    action="groups",
    args=[
        Arg(name="group_id", type="str", description="ID of the group", required=True),
        Arg(name="after", type="str", description="Pagination cursor", required=False),
        Arg(name="limit", type="int", description="Number of members to return (max 200)", required=False),
    ],
)

# Add Member to Group Tool
okta_add_member = OktaTool(
    name="add_member",
    description="Add a user to an Okta group",
    action="groups",
    args=[
        Arg(name="group_name", type="str", description="Name of the group to add the user to", required=True),
        Arg(name="user_id", type="str", description="ID or login of the user to add", required=True),
    ],
)

# Remove Member from Group Tool
okta_remove_member = OktaTool(
    name="remove_member",
    description="Remove a user from an Okta group",
    action="groups",
    args=[
        Arg(name="group_name", type="str", description="Name of the group to remove the user from", required=True),
        Arg(name="user_id", type="str", description="ID or login of the user to remove", required=True),
    ],
)

# List of all Okta tools
all_tools = [
    # User Tools
    okta_get_user,
    okta_search_users,
    okta_list_users,
    
    # Group Tools
    okta_list_groups,
    okta_create_group,
    okta_update_group,
    okta_delete_group,
    okta_get_group,
    okta_list_members,
    okta_add_member,
    okta_remove_member,
]

# Register all Okta tools
for tool in all_tools:
    tool_registry.register("okta", tool)