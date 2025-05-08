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
    # Handle both UUID and build number formats for pipeline_uuid
    if [[ "$pipeline_uuid" =~ ^[0-9]+$ ]]; then
        # If pipeline_uuid is numeric, first get the actual UUID
        PIPELINE_RESPONSE=$(curl -s -H "$BITBUCKET_AUTH_HEADER" \
            "https://api.bitbucket.org/2.0/repositories/$workspace/$repo/pipelines/?q=build_number=$pipeline_uuid")
        
        # Extract the UUID from the response
        ACTUAL_PIPELINE_UUID=$(echo "$PIPELINE_RESPONSE" | jq -r '.values[0].uuid // ""')
        
        if [ -z "$ACTUAL_PIPELINE_UUID" ] || [ "$ACTUAL_PIPELINE_UUID" == "null" ]; then
            echo "No pipeline found with build number $pipeline_uuid."
            exit 1
        fi
    else
        # If pipeline_uuid is already in UUID format, use it directly
        ACTUAL_PIPELINE_UUID="$pipeline_uuid"
    fi
    
    # Get logs using the actual UUID
    curl -s -H "$BITBUCKET_AUTH_HEADER" \
        "https://api.bitbucket.org/2.0/repositories/$workspace/$repo/pipelines/$ACTUAL_PIPELINE_UUID/steps/$step_uuid/log" | \
        jq -r '.content // "No logs available"'
    """,
    args=[
        Arg(name="workspace", type="str", description="Bitbucket workspace slug", required=True),
        Arg(name="repo", type="str", description="Repository name", required=True),
        Arg(name="pipeline_uuid", type="str", description="Pipeline UUID or build number", required=True),
        Arg(name="step_uuid", type="str", description="Step UUID", required=True),
    ],
)

pipeline_get = BitbucketCliTool(
    name="bitbucket_pipeline_get",
    description="Get details for a specific pipeline",
    content="""
    # Ensure pipeline_uuid is properly formatted
    # Bitbucket API expects UUIDs in the format {xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx}
    # If a numeric ID is provided, we need to query differently
    
    if [[ "$pipeline_uuid" =~ ^[0-9]+$ ]]; then
        # If pipeline_uuid is numeric, use the build_number endpoint
        RESPONSE=$(curl -s -H "$BITBUCKET_AUTH_HEADER" \
            "https://api.bitbucket.org/2.0/repositories/$workspace/$repo/pipelines/?q=build_number=$pipeline_uuid")
        
        # Extract the first pipeline from the results
        PIPELINE_DATA=$(echo "$RESPONSE" | jq '.values[0] // {}')
    else
        # If pipeline_uuid is already in UUID format, use it directly
        PIPELINE_DATA=$(curl -s -H "$BITBUCKET_AUTH_HEADER" \
            "https://api.bitbucket.org/2.0/repositories/$workspace/$repo/pipelines/$pipeline_uuid")
    fi
    
    # Format and output the pipeline data
    echo "$PIPELINE_DATA" | jq '{
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
        Arg(name="pipeline_uuid", type="str", description="Pipeline UUID or build number", required=True),
    ],
)

pipeline_steps = BitbucketCliTool(
    name="bitbucket_pipeline_steps",
    description="Get steps for a specific pipeline",
    content="""
    # Handle both UUID and build number formats
    if [[ "$pipeline_uuid" =~ ^[0-9]+$ ]]; then
        # If pipeline_uuid is numeric, first get the actual UUID
        PIPELINE_RESPONSE=$(curl -s -H "$BITBUCKET_AUTH_HEADER" \
            "https://api.bitbucket.org/2.0/repositories/$workspace/$repo/pipelines/?q=build_number=$pipeline_uuid")
        
        # Extract the UUID from the response
        ACTUAL_UUID=$(echo "$PIPELINE_RESPONSE" | jq -r '.values[0].uuid // ""')
        
        if [ -z "$ACTUAL_UUID" ] || [ "$ACTUAL_UUID" == "null" ]; then
            echo "No pipeline found with build number $pipeline_uuid."
            exit 1
        fi
        
        pipeline_uuid="$ACTUAL_UUID"
    fi
    
    # First, get the pipeline details to verify it exists
    PIPELINE_DETAILS=$(curl -s -H "$BITBUCKET_AUTH_HEADER" \
        "https://api.bitbucket.org/2.0/repositories/$workspace/$repo/pipelines/$pipeline_uuid")
    
    # Check if pipeline exists
    if echo "$PIPELINE_DETAILS" | jq -e '.error' > /dev/null 2>&1; then
        echo "Error retrieving pipeline details:"
        echo "$PIPELINE_DETAILS" | jq '.'
        exit 1
    fi
    
    # Now get the steps with proper error handling
    RESPONSE=$(curl -s -H "$BITBUCKET_AUTH_HEADER" \
        "https://api.bitbucket.org/2.0/repositories/$workspace/$repo/pipelines/$pipeline_uuid/steps/")
    
    # Check for API errors
    if echo "$RESPONSE" | jq -e '.error' > /dev/null 2>&1; then
        echo "API Error:"
        echo "$RESPONSE" | jq '.'
        exit 1
    fi
    
    # Check if the response contains values
    if echo "$RESPONSE" | jq -e '.values' > /dev/null 2>&1 && [ "$(echo "$RESPONSE" | jq '.values | length')" -gt 0 ]; then
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
        echo "No pipeline steps found for pipeline $pipeline_uuid."
        echo "Pipeline details:"
        echo "$PIPELINE_DETAILS" | jq '.'
    fi
    """,
    args=[
        Arg(name="workspace", type="str", description="Bitbucket workspace slug", required=True),
        Arg(name="repo", type="str", description="Repository name", required=True),
        Arg(name="pipeline_uuid", type="str", description="Pipeline UUID or build number", required=True),
    ],
)

# Register tools
for tool in [pipeline_list, pipeline_logs, pipeline_get, pipeline_steps]:
    tool_registry.register("bitbucket", tool)

__all__ = ['pipeline_list', 'pipeline_logs', 'pipeline_get', 'pipeline_steps'] 