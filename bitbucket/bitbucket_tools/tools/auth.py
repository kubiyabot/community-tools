from .base import BitbucketCliTool
from kubiya_workflow_sdk.tools.registry import tool_registry

auth_test = BitbucketCliTool(
    name="bitbucket_auth_test",
    description="Test Bitbucket authentication and list accessible workspaces",
    content="""
    # Test authentication and get user info
    echo "Testing authentication..."
    USER_INFO=$(curl -s -u $BITBUCKET_AUTH \
        "https://api.bitbucket.org/2.0/user" \
        -w "\\nStatus: %{http_code}")
    
    if echo "$USER_INFO" | grep -q "Status: 200"; then
        echo "✅ Authentication successful!"
        echo "User details:"
        echo "$USER_INFO" | sed '$d' | jq '{
            username: .username,
            display_name: .display_name,
            account_id: .account_id
        }'
        
        echo "\\nAccessible workspaces:"
        curl -s -u $BITBUCKET_AUTH \
            "https://api.bitbucket.org/2.0/workspaces" | \
            jq '.values[] | {
                name: .name,
                slug: .slug,
                is_private: .is_private
            }'
    else
        echo "❌ Authentication failed!"
        echo "$USER_INFO"
        exit 1
    fi
    """,
    args=[],
)

# Register tool
tool_registry.register("bitbucket", auth_test)

__all__ = ['auth_test'] 