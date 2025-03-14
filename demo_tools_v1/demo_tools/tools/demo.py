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
                DD_SITE="datadoghq.com"
            fi

            echo "Generating error spike demo data..."
            for i in {1..10}; do
                curl -X POST "https://http-intake.logs.$DD_SITE/api/v2/logs" \
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
                    ]'
                sleep 2
            done

            echo "✅ Generated 10 error spike log entries"
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
                DD_SITE="datadoghq.com"
            fi

            echo "Generating faulty deployment demo data..."
            for i in {1..10}; do
                curl -X POST "https://http-intake.logs.$DD_SITE/api/v2/logs" \
                    -H "DD-API_KEY: $DD_API_KEY" \
                    -H "Content-Type: application/json" \
                    -d '[
                        {
                            "ddsource": "kubiya-demo",
                            "service": "demo-service",
                            "status": "error",
                            "message": "⚠️ Deployment failure: Service degradation after deployment - '"$i"'",
                            "attributes": {
                                "log_category": "deployment-error",
                                "error_code": 503,
                                "deployment_id": "deploy-'"$i"'",
                                "affected_service": "demo-service",
                                "deployment_stage": "rollout"
                            }
                        }
                    ]'
                sleep 2
            done

            echo "✅ Generated 10 faulty deployment log entries"
            """
        )

# Initialize tools
DemoTools() 