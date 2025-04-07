from .base import GrafanaBaseTool, LoggingArgsMixin, MetricsArgsMixin
from kubiya_sdk.tools import Arg
from kubiya_sdk.tools.registry import tool_registry

class GrafanaLogTool(GrafanaBaseTool, LoggingArgsMixin):
    """Grafana tool with logging capabilities."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_common_log_args()

class GrafanaMetricTool(GrafanaBaseTool, MetricsArgsMixin):
    """Grafana tool with metrics capabilities."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_common_metric_args()

class GrafanaTools:
    """Grafana logging and visualization tools."""
    
    def __init__(self):
        """Initialize and register all Grafana tools."""
        tools = [
            self.search_logs(),
            self.get_dashboard(),
            self.export_panel(),
            self.get_metrics()
        ]
        
        for tool in tools:
            tool_registry.register("grafana", tool)

    def search_logs(self) -> GrafanaLogTool:
        """Search logs in Loki using a request_id label."""
        return GrafanaLogTool(
            name="search_logs",
            description="Search Loki logs in Grafana using request_id",
            content="""
            #!/bin/sh

            # Install jq if not present
            apk add --no-cache jq curl >/dev/null

            # Required envs
            if [ -z "$GRAFANA_API_TOKEN" ] || [ -z "$request_id" ]; then
                echo "Missing GRAFANA_API_TOKEN or request_id"
                exit 1
            fi

            GRAFANA_HOST=${GRAFANA_HOST:-localhost}
            DS_UID="fei7g5i1kjpj4e"  # Replace with your actual Loki datasource UID

            # Escape query properly
            QUERY=$(printf '{request_id="%s"}' "$request_id" | jq -sRr @uri)

            # Build query URL (use /query not /query_range to avoid time issues)
            URL="http://$GRAFANA_HOST/api/datasources/proxy/uid/$DS_UID/loki/api/v1/query?query=$QUERY"

            # Run the query
            RESPONSE=$(curl -s -H "Authorization: Bearer $GRAFANA_API_TOKEN" "$URL")

            # Output raw and parsed response
            echo "Raw Response:"
            echo "$RESPONSE"
            echo ""
            echo "$RESPONSE" | jq '.data.result[]?.values[]?[1]'
            """,
            args=[
                Arg(name="request_id", description="Request ID to search for", required=True)
            ]
        )


    def get_dashboard(self) -> GrafanaBaseTool:
        """Get Grafana dashboard by UID."""
        return GrafanaBaseTool(
            name="get_dashboard",
            description="Get Grafana dashboard details",
            content="""
            #!/usr/bin/env python3
            import os
            import json
            from grafana_api.grafana_face import GrafanaFace

            # Initialize Grafana client
            grafana = GrafanaFace(
                auth=os.environ['GRAFANA_API_TOKEN'],
                host=os.environ.get('GRAFANA_HOST', 'localhost')
            )

            # Get dashboard
            dashboard = grafana.dashboard.get_dashboard(
                os.environ['dashboard_uid']
            )
            print(json.dumps(dashboard))
            """,
            args=[
                Arg(name="dashboard_uid",
                    description="UID of the dashboard",
                    required=True)
            ]
        )

    def export_panel(self) -> GrafanaBaseTool:
        """Export a specific panel from a dashboard."""
        return GrafanaBaseTool(
            name="export_panel",
            description="Export a specific panel as PNG",
            content="""
            #!/usr/bin/env python3
            import os
            import base64
            from grafana_api.grafana_face import GrafanaFace

            # Initialize Grafana client
            grafana = GrafanaFace(
                auth=os.environ['GRAFANA_API_TOKEN'],
                host=os.environ.get('GRAFANA_HOST', 'localhost')
            )

            # Get panel image
            panel_png = grafana.dashboard.get_panel_png(
                dashboard_uid=os.environ['dashboard_uid'],
                panel_id=int(os.environ['panel_id']),
                width=int(os.environ.get('width', '1000')),
                height=int(os.environ.get('height', '500'))
            )

            # Convert to base64 for Slack
            print(base64.b64encode(panel_png).decode())
            """,
            args=[
                Arg(name="dashboard_uid",
                    description="UID of the dashboard",
                    required=True),
                Arg(name="panel_id",
                    description="ID of the panel to export",
                    required=True),
                Arg(name="width",
                    description="Width of the exported image",
                    required=False),
                Arg(name="height",
                    description="Height of the exported image",
                    required=False)
            ]
        )

    def get_metrics(self) -> GrafanaMetricTool:
        """Get metrics data from Grafana."""
        return GrafanaMetricTool(
            name="get_metrics",
            description="Get metrics data from Grafana",
            content="""
            #!/usr/bin/env python3
            import os
            import json
            from grafana_api.grafana_face import GrafanaFace
            from datetime import datetime, timezone

            # Initialize Grafana client
            grafana = GrafanaFace(
                auth=os.environ['GRAFANA_API_TOKEN'],
                host=os.environ.get('GRAFANA_HOST', 'localhost')
            )

            # Build query
            query = {
                'expr': os.environ['metric_name'],
                'step': os.environ.get('period', '60s')
            }

            if 'start_time' in os.environ:
                query['start'] = datetime.fromisoformat(os.environ['start_time'])
            if 'end_time' in os.environ:
                query['end'] = datetime.fromisoformat(os.environ['end_time'])

            # Execute query
            result = grafana.metrics.query(query)
            print(json.dumps(result, default=str))
            """,
        )

# Initialize when module is imported
GrafanaTools() 