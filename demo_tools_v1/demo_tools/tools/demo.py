from typing import List
from kubiya_sdk.tools.registry import tool_registry
from .base import DemoTool, Arg

class DemoTools:
    """Demo tools for generating test data."""

    def __init__(self):
        """Initialize and register demo tools."""
        try:
            tools = [
                self.get_error_spike_tool(),
                self.get_faulty_deployment_tool()
            ]
            
            for tool in tools:
                tool_registry.register("demo", tool)
                
        except Exception as e:
            print(f"❌ Failed to register demo tools: {str(e)}")
            raise

    def get_error_spike_tool(self) -> DemoTool:
        """Get the error spike generation tool."""
        return DemoTool(
            name="generate_error_spike",
            description="Generate sample error spike data for demonstration",
            content="""
            if [ -z "$DD_API_KEY" ]; then
                echo "Error: DD_API_KEY environment variable is required"
                exit 1
            fi

            if [ -z "$DD_SITE" ]; then
                echo "Error: DD_SITE environment variable is required"
                exit 1
            fi

            echo "Generating error spike demo data..."
            successful_submissions=0
            failed_submissions=0

            for i in $(seq 1 10); do
                echo "Sending log entry $i/10..."
                response=$(curl -s -w "\\n%{http_code}" -X POST "https://http-intake.logs.$DD_SITE/api/v2/logs" \
                    -H "DD-API-KEY: $DD_API_KEY" \
                    -H "Content-Type: application/json" \
                    -d '[
                        {
                            "ddsource": "kubiya-demo",
                            "service": "demo-service",
                            "status": "error",
                            "message": "🔥 API error detected: Increased failure rate on /api/orders - '"$i"'",
                            "attributes": {
                                "log_category": "error-spike",
                                "error_code": 500,
                                "affected_endpoint": "/api/orders",
                                "latency_ms": 850,
                                "database_slowdown": true
                            }
                        }
                    ]')

                http_code=$(echo "$response" | tail -n1)
                if [ "$http_code" = "202" ]; then
                    successful_submissions=$((successful_submissions + 1))
                    echo "✅ Log entry $i submitted successfully"
                else
                    failed_submissions=$((failed_submissions + 1))
                    echo "❌ Failed to submit log entry $i (HTTP $http_code)"
                fi
                sleep 2
            done

            echo "📊 Summary:"
            echo "- Successful submissions: $successful_submissions"
            echo "- Failed submissions: $failed_submissions"

            if [ "$failed_submissions" -gt 0 ]; then
                echo "⚠️ Warning: Some submissions failed"
                exit 1
            else
                echo "✅ All $successful_submissions error spike log entries were generated successfully"
            fi
            """
        )

    def get_faulty_deployment_tool(self) -> DemoTool:
        """Get the faulty deployment generation tool."""
        return DemoTool(
            name="generate_faulty_deployment",
            description="Generate sample faulty deployment data for demonstration",
            content="""
            if [ -z "$DD_API_KEY" ]; then
                echo "Error: DD_API_KEY environment variable is required"
                exit 1
            fi

            if [ -z "$DD_SITE" ]; then
                echo "Error: DD_SITE environment variable is required"
                exit 1
            fi

            echo "Generating faulty deployment demo data..."
            successful_submissions=0
            failed_submissions=0

            for i in $(seq 1 10); do
                echo "Sending log entry $i/10..."
                response=$(curl -s -w "\\n%{http_code}" -X POST "https://http-intake.logs.$DD_SITE/api/v2/logs" \
                    -H "DD-API-KEY: $DD_API_KEY" \
                    -H "Content-Type: application/json" \
                    -d '[
                        {
                            "ddsource": "kubiya-demo",
                            "service": "demo-service",
                            "status": "error",
                            "message": "⚠️ Deployment failure: Service degradation after deployment - '"$i"'",
                            "attributes": {
                                "log_category": "deployment-failure",
                                "error_code": 503,
                                "deployment_id": "deploy-'"$i"'",
                                "affected_service": "demo-service",
                                "deployment_stage": "rollout"
                            }
                        }
                    ]')

                http_code=$(echo "$response" | tail -n1)
                if [ "$http_code" = "202" ]; then
                    successful_submissions=$((successful_submissions + 1))
                    echo "✅ Log entry $i submitted successfully"
                else
                    failed_submissions=$((failed_submissions + 1))
                    echo "❌ Failed to submit log entry $i (HTTP $http_code)"
                fi
                sleep 2
            done

            echo "📊 Summary:"
            echo "- Successful submissions: $successful_submissions"
            echo "- Failed submissions: $failed_submissions"

            if [ "$failed_submissions" -gt 0 ]; then
                echo "⚠️ Warning: Some submissions failed"
                exit 1
            else
                echo "✅ All $successful_submissions faulty deployment log entries were generated successfully"
            fi
            """
        )

# Initialize tools
DemoTools() 