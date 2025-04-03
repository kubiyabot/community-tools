from kubiya_sdk.tools import Arg
from .base import AWSCliTool
from kubiya_sdk.tools.registry import tool_registry

athena_query_logs = AWSCliTool(
    name="athena_query_logs",
    description="Query logs using Athena by scanning log files stored in S3",
    content="""
# List all log files in the prefix
LOG_FILES=$(aws s3api list-objects \
    --bucket "$bucket" \
    --prefix "$prefix" \
    --query "Contents[].Key" \
    --output text)

MATCHES=""

# Loop over each file and search for the pattern
for FILE in $LOG_FILES; do
    LOG_CONTENT=$(aws s3 cp s3://$bucket/$FILE -)
    if echo "$LOG_CONTENT" | grep -q "$search"; then
        MATCHES="$MATCHES\\n\\n---\\nFile: $FILE\\n$(echo "$LOG_CONTENT" | grep "$search")"
    fi
done

# Output results
if [ -n "$MATCHES" ]; then
    echo -e "Athena Query Results:$MATCHES"
else
    echo "No matches found for pattern: $search"
fi
""",
    args=[
        Arg(name="bucket", type="str", description="S3 bucket name (e.g. demo-app-logs)", required=True),
        Arg(name="prefix", type="str", description="S3 prefix to search (e.g. logs/ or logs/worker/)", required=True),
        Arg(name="search", type="str", description="Pattern to search for in log files (e.g. ERROR, user_id)", required=True),
    ],
)

tool_registry.register("aws", athena_query_logs)
