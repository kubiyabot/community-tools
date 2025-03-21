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
        """Search logs with specific criteria."""
        return GrafanaLogTool(
            name="search_logs",
            description="Search Grafana logs with specific criteria",
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
                'expr': f'{{request_id="{os.environ["request_id"]}"}}',
                'limit': int(os.environ.get('limit', '100'))
            }

            if 'start_time' in os.environ:
                query['start'] = datetime.fromisoformat(os.environ['start_time'])
            if 'end_time' in os.environ:
                query['end'] = datetime.fromisoformat(os.environ['end_time'])

            # Execute query
            result = grafana.search.search_logs(query)
            print(json.dumps(result, default=str))
            """,
            args=[
                Arg(name="request_id",
                    description="Request ID to search for",
                    required=True)
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