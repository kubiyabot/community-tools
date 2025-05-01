from kubiya_sdk.tools import Arg
from .base import BitbucketCliTool
from kubiya_sdk.tools.registry import tool_registry

commit_create = BitbucketCliTool(
    name="bitbucket_commit_create",
    description="Create a commit with multiple file changes",
    content="""
    # Create a temporary directory for the files
    TEMP_DIR=$(mktemp -d)
    
    # Process the files array
    echo "$files" | jq -c '.[]' | while read -r file; do
        path=$(echo "$file" | jq -r '.path')
        content=$(echo "$file" | jq -r '.content')
        
        # Create directory structure if needed
        mkdir -p "$TEMP_DIR/$(dirname "$path")"
        echo "$content" > "$TEMP_DIR/$path"
    done

    # Create the commit
    cd "$TEMP_DIR"
    curl -X POST -H "$BITBUCKET_AUTH_HEADER" \
        -H "Content-Type: multipart/form-data" \
        -F "message=$commit_message" \
        -F "branch=$branch" \
        -F "author.name=$BITBUCKET_USERNAME" \
        -F "author.email=${BITBUCKET_EMAIL:-$BITBUCKET_USERNAME@users.noreply.bitbucket.org}" \
        $(find . -type f -exec echo "-F \"file=@{}\"" \;) \
        "https://api.bitbucket.org/2.0/repositories/$workspace/$repo/src"

    # Cleanup
    rm -rf "$TEMP_DIR"
    """,
    args=[
        Arg(name="workspace", type="str", description="Bitbucket workspace slug", required=True),
        Arg(name="repo", type="str", description="Repository name", required=True),
        Arg(name="branch", type="str", description="Branch to commit to", required=True),
        Arg(name="commit_message", type="str", description="Commit message", required=True),
        Arg(name="files", type="str", description="JSON string array of files to commit, each with 'path' and 'content' fields. Format: '[{\"path\":\"file.txt\",\"content\":\"file content\"}]'", required=True),
    ],
)

commit_get = BitbucketCliTool(
    name="bitbucket_commit_get",
    description="Get details of a specific commit",
    content="""
    curl -s -H "$BITBUCKET_AUTH_HEADER" \
        "https://api.bitbucket.org/2.0/repositories/$workspace/$repo/commit/$commit" | \
        jq '{
            hash: .hash,
            message: .message,
            date: .date,
            author: .author.raw,
            parents: [.parents[].hash]
        }'
    """,
    args=[
        Arg(name="workspace", type="str", description="Bitbucket workspace slug", required=True),
        Arg(name="repo", type="str", description="Repository name", required=True),
        Arg(name="commit", type="str", description="Commit hash", required=True),
    ],
)

commit_list = BitbucketCliTool(
    name="bitbucket_commit_list",
    description="List commits in a repository",
    content="""
    curl -s -H "$BITBUCKET_AUTH_HEADER" \
        "https://api.bitbucket.org/2.0/repositories/$workspace/$repo/commits/$branch" | \
        jq '.values[] | {
            hash: .hash,
            message: .message,
            date: .date,
            author: .author.raw
        }'
    """,
    args=[
        Arg(name="workspace", type="str", description="Bitbucket workspace slug", required=True),
        Arg(name="repo", type="str", description="Repository name", required=True),
        Arg(name="branch", type="str", description="Branch to list commits from", required=True),
    ],
)

commit_comment = BitbucketCliTool(
    name="bitbucket_commit_comment",
    description="Add a comment to a commit",
    content="""
    curl -X POST -H "$BITBUCKET_AUTH_HEADER" \
        -H "Content-Type: application/json" \
        -d '{
            "content": {
                "raw": "'$comment'"
            }
        }' \
        "https://api.bitbucket.org/2.0/repositories/$workspace/$repo/commit/$commit_hash/comments"
    """,
    args=[
        Arg(name="workspace", type="str", description="Bitbucket workspace slug", required=True),
        Arg(name="repo", type="str", description="Repository name", required=True),
        Arg(name="commit_hash", type="str", description="Commit hash", required=True),
        Arg(name="comment", type="str", description="Comment content (markdown supported)", required=True),
    ],
)

# Register tools
for tool in [commit_create, commit_get, commit_list, commit_comment]:
    tool_registry.register("bitbucket", tool)

__all__ = ['commit_create', 'commit_get', 'commit_list', 'commit_comment']