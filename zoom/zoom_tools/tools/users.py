from kubiya_sdk.tools import Arg
from kubiya_sdk.tools.registry import tool_registry
from .base import ZoomTool

list_users_tool = ZoomTool(
    name="list-zoom-users",
    description="List all users in the Zoom account",
    mermaid="""
    flowchart TD
        Z[Zoom API] --> U1[User 1 👤]
        Z --> U2[User 2 👤]
        Z --> U3[User 3 👤]
        
        U1 --> D1[User Details]
        U2 --> D2[User Details]
        U3 --> D3[User Details]
        
        style Z fill:#f96,stroke:#333,stroke-width:4px
        style U1 fill:#bbf,stroke:#333
        style U2 fill:#bbf,stroke:#333
        style U3 fill:#bbf,stroke:#333
    """,
    content="""
        #!/usr/bin/env python3
        from zoom_helpers import get_zoom_client, handle_zoom_response
        
        client = get_zoom_client()
        status = os.environ.get('status', 'active')  # active, inactive, pending
        
        print(f"👥 Fetching {status} users...")
        
        response = client.user.list(status=status)
        data = handle_zoom_response(response, "Users retrieved successfully")
        
        users = data.get('users', [])
        print(f"Found {len(users)} users")
        
        for user in users:
            print(f"\n👤 User: {user['email']}")
            print(f"   • Name: {user['first_name']} {user['last_name']}")
            print(f"   • Type: {user['type']}")
            print(f"   • Status: {user['status']}")
            print(f"   • Created: {user['created_at']}")
    """,
    args=[
        Arg(name="status", description="User status to filter by (active, inactive, pending)", required=False, default="active"),
    ]
)

# Add more user management tools here
tool_registry.register("zoom", list_users_tool) 