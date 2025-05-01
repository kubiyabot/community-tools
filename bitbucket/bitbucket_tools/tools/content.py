from kubiya_sdk.tools import Arg
from .base import BitbucketCliTool
from kubiya_sdk.tools.registry import tool_registry

content_create = BitbucketCliTool(
    name="bitbucket_content_create",
    description="Create or update a file in a Bitbucket repository",
    content="""
    # Create a temporary file with the content
    TEMP_FILE=$(mktemp)
    echo "$content" > "$TEMP_FILE"

    # Encode content in base64
    CONTENT_B64=$(base64 "$TEMP_FILE")

    curl -X POST -H "$BITBUCKET_AUTH_HEADER" \
        -H "Content-Type: application/json" \
        -d '{
            "message": "'$commit_message'",
            "branch": "'$branch'",
            "content": "'$CONTENT_B64'",
            "author": {
                "name": "'${BITBUCKET_USERNAME}'",
                "email": "'${BITBUCKET_EMAIL:-$BITBUCKET_USERNAME@users.noreply.bitbucket.org}'"
            }
        }' \
        "https://api.bitbucket.org/2.0/repositories/$workspace/$repo/src"

    rm -f "$TEMP_FILE"
    """,
    args=[
        Arg(name="workspace", type="str", description="Bitbucket workspace slug", required=True),
        Arg(name="repo", type="str", description="Repository name", required=True),
        Arg(name="path", type="str", description="Path to the file in the repository", required=True),
        Arg(name="content", type="str", description="Content to write to the file", required=True),
        Arg(name="branch", type="str", description="Branch to commit to", required=True),
        Arg(name="commit_message", type="str", description="Commit message", required=True),
    ],
)

content_get = BitbucketCliTool(
    name="bitbucket_content_get",
    description="Get the contents of a file from a Bitbucket repository",
    content="""
    curl -s -H "$BITBUCKET_AUTH_HEADER" \
        "https://api.bitbucket.org/2.0/repositories/$workspace/$repo/src/$ref/$path" | \
        jq -r '.content'
    """,
    args=[
        Arg(name="workspace", type="str", description="Bitbucket workspace slug", required=True),
        Arg(name="repo", type="str", description="Repository name", required=True),
        Arg(name="path", type="str", description="Path to the file in the repository", required=True),
        Arg(name="ref", type="str", description="Branch, tag, or commit", required=True),
    ],
)

content_delete = BitbucketCliTool(
    name="bitbucket_content_delete",
    description="Delete a file from a Bitbucket repository",
    content="""
    curl -X DELETE -H "$BITBUCKET_AUTH_HEADER" \
        -H "Content-Type: application/json" \
        -d '{
            "message": "'$commit_message'",
            "branch": "'$branch'",
            "author": {
                "name": "'${BITBUCKET_USERNAME}'",
                "email": "'${BITBUCKET_EMAIL:-$BITBUCKET_USERNAME@users.noreply.bitbucket.org}'"
            }
        }' \
        "https://api.bitbucket.org/2.0/repositories/$workspace/$repo/src/$path"
    """,
    args=[
        Arg(name="workspace", type="str", description="Bitbucket workspace slug", required=True),
        Arg(name="repo", type="str", description="Repository name", required=True),
        Arg(name="path", type="str", description="Path to the file to delete", required=True),
        Arg(name="branch", type="str", description="Branch to commit to", required=True),
        Arg(name="commit_message", type="str", description="Commit message", required=True),
    ],
)

# Register tools
for tool in [content_create, content_get, content_delete]:
    tool_registry.register("bitbucket", tool)

__all__ = ['content_create', 'content_get', 'content_delete'] 