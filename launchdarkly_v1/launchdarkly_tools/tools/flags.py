from typing import List
import sys
from .base import LaunchDarklyTool, Arg
from kubiya_sdk.tools.registry import tool_registry

class FlagAnalyzer:
    """Analyze LaunchDarkly feature flags."""
    
    def __init__(self):
        """Initialize and register all tools."""
        try:
            # Create and register tools
            tools = [
                self.get_flag_status(),
                self.list_flags(),
                self.get_flag_history(),
                self.compare_flag_states()
            ]
            
            for tool in tools:
                try:
                    tool_registry.register("launchdarkly", tool)
                    print(f"✅ Registered: {tool.name}")
                except Exception as e:
                    print(f"❌ Failed to register {tool.name}: {str(e)}", file=sys.stderr)
                    raise

        except Exception as e:
            print(f"❌ Failed to register LaunchDarkly tools: {str(e)}", file=sys.stderr)
            raise

    def get_flag_status(self) -> LaunchDarklyTool:
        """Get the current status of a feature flag."""
        return LaunchDarklyTool(
            name="get_flag_status",
            description="Get the current status of a feature flag",
            content="""
            if [ -z "$flag_key" ]; then
                echo "Error: Flag key is required"
                exit 1
            fi

            # Validate LaunchDarkly connection
            validate_launchdarkly_connection

            # Get flag details
            curl -s -H "Authorization: $LD_API_KEY" \
                "https://app.launchdarkly.com/api/v2/flags/$PROJECT_KEY/$flag_key" | \
                jq '{ 
                    key: .key,
                    name: .name,
                    description: .description,
                    kind: .kind,
                    enabled: .enabled,
                    variations: .variations,
                    environments: .environments
                }'
            """,
            args=[
                Arg(name="flag_key",
                    description="Key of the feature flag",
                    required=True),
                Arg(name="environment",
                    description="Environment to check (default: production)",
                    required=False)
            ],
            image="curlimages/curl:8.1.2"
        )

    def list_flags(self) -> LaunchDarklyTool:
        """List all feature flags in a project."""
        return LaunchDarklyTool(
            name="list_flags",
            description="List all feature flags in a project",
            content="""
            # Validate LaunchDarkly connection
            validate_launchdarkly_connection

            # Build query parameters
            QUERY=""
            if [ ! -z "$status" ]; then
                QUERY="?status=$status"
            fi
            if [ ! -z "$tag" ]; then
                QUERY="${QUERY:+$QUERY&}tag=$tag"
            fi

            # Get flags list
            curl -s -H "Authorization: $LD_API_KEY" \
                "https://app.launchdarkly.com/api/v2/flags/$PROJECT_KEY$QUERY" | \
                jq '.items[] | {
                    key: .key,
                    name: .name,
                    enabled: .enabled,
                    tags: .tags,
                    maintainer: .maintainerId,
                    createdDate: .creationDate
                }'
            """,
            args=[
                Arg(name="status",
                    description="Filter by flag status (active/archived)",
                    required=False),
                Arg(name="tag",
                    description="Filter by tag",
                    required=False)
            ],
            image="curlimages/curl:8.1.2"
        )

    def get_flag_history(self) -> LaunchDarklyTool:
        """Get the change history of a feature flag."""
        return LaunchDarklyTool(
            name="get_flag_history",
            description="Get the change history of a feature flag",
            content="""
            if [ -z "$flag_key" ]; then
                echo "Error: Flag key is required"
                exit 1
            fi

            # Validate LaunchDarkly connection
            validate_launchdarkly_connection

            # Set default limit if not provided
            LIMIT=${limit:-50}
            
            # Get flag audit log with error handling
            RESPONSE=$(curl -s -w "\\n%{http_code}" -H "Authorization: $LD_API_KEY" \
                "https://app.launchdarkly.com/api/v2/auditlog/$PROJECT_KEY/flags/$flag_key?limit=$LIMIT")
            
            HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
            BODY=$(echo "$RESPONSE" | sed '$ d')
            
            if [ "$HTTP_CODE" != "200" ]; then
                echo "Error: Failed to fetch flag history. HTTP Code: $HTTP_CODE"
                echo "Response: $BODY"
                exit 1
            fi
            
            # Check if response is empty
            if [ -z "$BODY" ] || [ "$BODY" = "null" ]; then
                echo "No history found for flag: $flag_key"
                exit 0
            fi
            
            # Process the response with error handling
            echo "$BODY" | jq --exit-status '.items[] | {
                date: .date,
                action: .action,
                member: (.member.email // "System"),
                description: .description,
                changes: .changes
            }' || {
                echo "Error: Failed to parse flag history"
                echo "Raw response: $BODY"
                exit 1
            }
            """,
            args=[
                Arg(name="flag_key",
                    description="Key of the feature flag",
                    required=True),
                Arg(name="limit",
                    description="Number of history entries to return (default: 50)",
                    required=False)
            ],
            image="curlimages/curl:8.1.2"
        )

    def compare_flag_states(self) -> LaunchDarklyTool:
        """Compare flag states between environments."""
        return LaunchDarklyTool(
            name="compare_flag_states",
            description="Compare flag states between environments",
            content="""
            if [ -z "$flag_key" ] || [ -z "$env1" ] || [ -z "$env2" ]; then
                echo "Error: Flag key and both environments are required"
                exit 1
            fi

            # Validate LaunchDarkly connection
            validate_launchdarkly_connection

            # Get flag states in both environments
            ENV1_STATE=$(curl -s -H "Authorization: $LD_API_KEY" \
                "https://app.launchdarkly.com/api/v2/flags/$PROJECT_KEY/$flag_key/environments/$env1")
            ENV2_STATE=$(curl -s -H "Authorization: $LD_API_KEY" \
                "https://app.launchdarkly.com/api/v2/flags/$PROJECT_KEY/$flag_key/environments/$env2")

            echo "=== Flag Comparison ==="
            echo "Flag: $flag_key"
            echo "\n$env1 Environment:"
            echo "$ENV1_STATE" | jq '{
                enabled: .enabled,
                version: .version,
                lastModified: .lastModified,
                targets: .targets,
                rules: .rules
            }'

            echo "\n$env2 Environment:"
            echo "$ENV2_STATE" | jq '{
                enabled: .enabled,
                version: .version,
                lastModified: .lastModified,
                targets: .targets,
                rules: .rules
            }'
            """,
            args=[
                Arg(name="flag_key",
                    description="Key of the feature flag",
                    required=True),
                Arg(name="env1",
                    description="First environment to compare",
                    required=True),
                Arg(name="env2",
                    description="Second environment to compare",
                    required=True)
            ],
            image="curlimages/curl:8.1.2"
        )

# Initialize when module is imported
FlagAnalyzer() 