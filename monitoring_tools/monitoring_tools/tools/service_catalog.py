from .base import MonitoringTool
from kubiya_sdk.tools import Arg
from kubiya_sdk.tools.registry import tool_registry

class ServiceCatalogTools:
    """Service catalog lookup tools."""
    
    def __init__(self):
        """Initialize and register all service catalog tools."""
        tools = [
            self.get_service_info()
        ]
        
        for tool in tools:
            tool_registry.register("service_catalog", tool)

    def get_service_info(self) -> MonitoringTool:
        """Get service information including repository, team, and other metadata."""
        return MonitoringTool(
            name="get_service_info",
            description="Get service metadata from service catalog",
            content="""
            #!/usr/bin/env python3
            import os
            import json

            SERVICE_CATALOG = {
                "payment-api": {
                    "repository": "organization/payment-service",
                    "team": "payments",
                    "oncall_rotation": "payments-oncall",
                    "slack_channel": "payments-alerts"
                },
                "user-service": {
                    "repository": "organization/user-management",
                    "team": "identity",
                    "oncall_rotation": "identity-oncall",
                    "slack_channel": "identity-alerts"
                }
            }

            service_name = os.environ['service_name']
            
            # Look up service info
            service_info = SERVICE_CATALOG.get(service_name)
            if not service_info:
                print(json.dumps({
                    "error": f"Service {service_name} not found in catalog"
                }))
                exit(1)
                
            print(json.dumps(service_info))
            """,
            args=[
                Arg(name="service_name",
                    description="Name of the service to look up",
                    required=True)
            ]
        )

# Initialize when module is imported
ServiceCatalogTools() 