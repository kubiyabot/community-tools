from kubiya_sdk.tools import Arg
from .base import BitbucketCliTool
from kubiya_sdk.tools.registry import tool_registry

pipeline_list = BitbucketCliTool(
    name="bitbucket_pipeline_list",
    description="List pipeline results for a repository",
    content="""
    curl -s -H "$BITBUCKET_AUTH_HEADER" \
        "https://api.bitbucket.org/2.0/repositories/$workspace/$repo/pipelines/" | \
        jq '.values[] | {uuid, state, created_on, target: .target.ref_name}'
    """,
    args=[
        Arg(name="workspace", type="str", description="Bitbucket workspace slug", required=True),
        Arg(name="repo", type="str", description="Repository name", required=True),
    ],
)

pipeline_logs = BitbucketCliTool(
    name="bitbucket_pipeline_logs",
    description="Get logs for a specific pipeline",
    content="""
    curl -s -H "$BITBUCKET_AUTH_HEADER" \
        "https://api.bitbucket.org/2.0/repositories/$workspace/$repo/pipelines/$pipeline_uuid/steps/$step_uuid/log" | \
        jq -r '.content // "No logs available"'
    """,
    args=[
        Arg(name="workspace", type="str", description="Bitbucket workspace slug", required=True),
        Arg(name="repo", type="str", description="Repository name", required=True),
        Arg(name="pipeline_uuid", type="str", description="Pipeline UUID", required=True),
        Arg(name="step_uuid", type="str", description="Step UUID", required=True),
    ],
)

pipeline_get = BitbucketCliTool(
    name="bitbucket_pipeline_get",
    description="Get details for a specific pipeline",
    content="""
    curl -s -H "$BITBUCKET_AUTH_HEADER" \
        "https://api.bitbucket.org/2.0/repositories/$workspace/$repo/pipelines/$pipeline_uuid" | \
        jq '{
            uuid: .uuid,
            state: .state,
            created_on: .created_on,
            completed_on: .completed_on,
            target: .target.ref_name,
            build_number: .build_number
        }'
    """,
    args=[
        Arg(name="workspace", type="str", description="Bitbucket workspace slug", required=True),
        Arg(name="repo", type="str", description="Repository name", required=True),
        Arg(name="pipeline_uuid", type="str", description="Pipeline UUID", required=True),
    ],
)

pipeline_steps = BitbucketCliTool(
    name="bitbucket_pipeline_steps",
    description="Get steps for a specific pipeline",
    content="""
    # Fetch the pipeline steps
    RESPONSE=$(curl -s -H "$BITBUCKET_AUTH_HEADER" \
        "https://api.bitbucket.org/2.0/repositories/$workspace/$repo/pipelines/$pipeline_uuid/steps/")
    
    # Check if the response contains values
    if echo "$RESPONSE" | jq -e '.values' > /dev/null 2>&1; then
        # Process the values if they exist
        echo "$RESPONSE" | jq '.values[] | {
            uuid: .uuid,
            name: .name,
            state: .state,
            started_on: .started_on,
            completed_on: .completed_on,
            duration_in_seconds: .duration_in_seconds
        }'
    else
        # Print the raw response for debugging
        echo "API Response:"
        echo "$RESPONSE" | jq '.'
        echo "No pipeline steps found or invalid response format."
    fi
    """,
    args=[
        Arg(name="workspace", type="str", description="Bitbucket workspace slug", required=True),
        Arg(name="repo", type="str", description="Repository name", required=True),
        Arg(name="pipeline_uuid", type="str", description="Pipeline UUID", required=True),
    ],
)

# Register tools
for tool in [pipeline_list, pipeline_logs, pipeline_get, pipeline_steps]:
    tool_registry.register("bitbucket", tool)

__all__ = ['pipeline_list', 'pipeline_logs', 'pipeline_get', 'pipeline_steps'] 