from typing import List
from .base import MonitoringTool
from kubiya_sdk.tools import Arg
from kubiya_sdk.tools.registry import tool_registry

class NewRelicTools:
    """New Relic monitoring and error tracking tools."""
    
    def __init__(self):
        """Initialize and register all New Relic tools."""
        tools = [
            self.get_error_details(),
            self.search_errors(),
            self.get_transaction_trace()
        ]
        
        for tool in tools:
            tool_registry.register("newrelic", tool)

    def get_error_details(self) -> MonitoringTool:
        """Get detailed information about a specific error."""
        return MonitoringTool(
            name="get_error_details",
            description="Get detailed information about a specific error",
            content="""
            if [ -z "$error_id" ]; then
                echo "Error: Error ID is required"
                exit 1
            fi

            curl -X GET "https://api.newrelic.com/v2/errors/$error_id" \
                -H "X-Api-Key: $NEWRELIC_API_KEY" \
                -H "Accept: application/json"
            """,
            args=[
                Arg(name="error_id",
                    description="ID of the error to investigate",
                    required=True)
            ],
            image="curlimages/curl:8.1.2"
        )

    def search_errors(self) -> MonitoringTool:
        """Search for errors based on criteria."""
        return MonitoringTool(
            name="search_errors",
            description="Search for errors based on criteria",
            content="""
            QUERY_PARAMS=""
            if [ ! -z "$error_type" ]; then
                QUERY_PARAMS="$QUERY_PARAMS&filter[error.type]=$error_type"
            fi
            if [ ! -z "$service" ]; then
                QUERY_PARAMS="$QUERY_PARAMS&filter[service.name]=$service"
            fi

            curl -X GET "https://api.newrelic.com/v2/errors?$QUERY_PARAMS" \
                -H "X-Api-Key: $NEWRELIC_API_KEY" \
                -H "Accept: application/json"
            """,
            args=[
                Arg(name="error_type",
                    description="Type of error to search for",
                    required=False),
                Arg(name="service",
                    description="Service name to filter by",
                    required=False)
            ],
            image="curlimages/curl:8.1.2"
        )

    def get_transaction_trace(self) -> MonitoringTool:
        """Get transaction trace details."""
        return MonitoringTool(
            name="get_transaction_trace",
            description="Get transaction trace details",
            content="""
            if [ -z "$transaction_id" ]; then
                echo "Error: Transaction ID is required"
                exit 1
            fi

            curl -X GET "https://api.newrelic.com/v2/transactions/$transaction_id/trace" \
                -H "X-Api-Key: $NEWRELIC_API_KEY" \
                -H "Accept: application/json"
            """,
            args=[
                Arg(name="transaction_id",
                    description="ID of the transaction to trace",
                    required=True)
            ],
            image="curlimages/curl:8.1.2"
        )

# Initialize when module is imported
NewRelicTools() 