from kubiya_sdk.tools import Arg
from .base import AWSCliTool
from kubiya_sdk.tools.registry import tool_registry

athena_query_logs = AWSCliTool(
    name="athena_query_logs",
    description="Query logs using Athena",
    content="""
    # Start query execution
    QUERY_ID=$(aws athena start-query-execution \
        --query-string "$query" \
        --query-execution-context Database=$database \
        --result-configuration OutputLocation=$output_location \
        --query 'QueryExecutionId' \
        --output text)
    
    # Wait for query completion
    while true; do
        STATUS=$(aws athena get-query-execution \
            --query-execution-id $QUERY_ID \
            --query 'QueryExecution.Status.State' \
            --output text)
        
        if [ "$STATUS" = "SUCCEEDED" ] || [ "$STATUS" = "FAILED" ] || [ "$STATUS" = "CANCELLED" ]; then
            break
        fi
        sleep 1
    done
    
    # Get results if successful
    if [ "$STATUS" = "SUCCEEDED" ]; then
        aws athena get-query-results --query-execution-id $QUERY_ID
    else
        ERROR=$(aws athena get-query-execution \
            --query-execution-id $QUERY_ID \
            --query 'QueryExecution.Status.StateChangeReason' \
            --output text)
        echo "Query failed: $ERROR"
        exit 1
    fi
    """,
    args=[
        Arg(name="database", type="str", description="Athena database name", required=True),
        Arg(name="query", type="str", description="SQL query", required=True),
        Arg(name="output_location", type="str", description="S3 output location", required=True),
    ],
)

tool_registry.register("aws", athena_query_logs) 