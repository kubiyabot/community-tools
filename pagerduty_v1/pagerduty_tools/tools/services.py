from typing import List
from .base import PagerDutyTool, Arg
from kubiya_sdk.tools.registry import tool_registry
import sys

class ServiceManager:
    """Manage PagerDuty service-related read operations."""
    
    def __init__(self):
        """Initialize and register all tools."""
        try:
            tools = [
                self.get_service_details(),
                self.list_service_metrics(),
                self.get_service_integrations(),
                self.get_service_maintenance_windows(),
                self.get_service_dependencies(),
                self.get_service_alerts(),
                self.get_service_statistics(),
                self.list_services(),
                self.list_service_event_rules(),
                self.list_service_change_events(),
                self.search_services(),
                self.list_service_standards()
            ]
            
            for tool in tools:
                try:
                    tool_registry.register("pagerduty", tool)
                    print(f"✅ Registered: {tool.name}")
                except Exception as e:
                    print(f"❌ Failed to register {tool.name}: {str(e)}", file=sys.stderr)
                    raise

        except Exception as e:
            print(f"❌ Failed to register PagerDuty service tools: {str(e)}", file=sys.stderr)
            raise

    def get_service_details(self) -> PagerDutyTool:
        """Get detailed information about a specific service."""
        return PagerDutyTool(
            name="get_service_details",
            description="Get detailed information about a specific PagerDuty service",
            content="""#!/bin/bash
if [ -z "$service_id" ]; then
    echo "Error: Service ID is required"
    exit 1
fi

curl -s \
  "https://api.pagerduty.com/services/${service_id}?include[]=escalation_policies&include[]=teams" \
  -H 'Accept: application/vnd.pagerduty+json;version=2' \
  -H "Authorization: Token token=${PD_API_KEY}"
""",
            args=[
                Arg(name="service_id",
                    description="ID of the service to get details for",
                    required=True)
            ]
        )

    def list_service_metrics(self) -> PagerDutyTool:
        """Get metrics for a specific service."""
        return PagerDutyTool(
            name="list_service_metrics",
            description="Get metrics and statistics for a specific service",
            content="""#!/bin/bash
if [ -z "$service_id" ]; then
    echo "Error: Service ID is required"
    exit 1
fi

since=${since:-$(date -v-30d -u +"%Y-%m-%dT%H:%M:%SZ")}
until=${until:-$(date -u +"%Y-%m-%dT%H:%M:%SZ")}

curl -s \
  "https://api.pagerduty.com/analytics/metrics/incidents/services/${service_id}?time_zone=UTC&start_time=${since}&end_time=${until}" \
  -H 'Accept: application/vnd.pagerduty+json;version=2' \
  -H "Authorization: Token token=${PD_API_KEY}"
""",
            args=[
                Arg(name="service_id",
                    description="ID of the service to get metrics for",
                    required=True),
                Arg(name="since",
                    description="Start date in ISO8601 format. Defaults to 30 days ago",
                    required=False),
                Arg(name="until",
                    description="End date in ISO8601 format. Defaults to current time",
                    required=False)
            ]
        )

    def get_service_integrations(self) -> PagerDutyTool:
        """List integrations for a specific service."""
        return PagerDutyTool(
            name="get_service_integrations",
            description="List all integrations for a specific service",
            content="""#!/bin/bash
if [ -z "$service_id" ]; then
    echo "Error: Service ID is required"
    exit 1
fi

curl -s \
  "https://api.pagerduty.com/services/${service_id}/integrations" \
  -H 'Accept: application/vnd.pagerduty+json;version=2' \
  -H "Authorization: Token token=${PD_API_KEY}"
""",
            args=[
                Arg(name="service_id",
                    description="ID of the service to get integrations for",
                    required=True)
            ]
        )

    def get_service_maintenance_windows(self) -> PagerDutyTool:
        """Get maintenance windows for a service."""
        return PagerDutyTool(
            name="get_service_maintenance_windows",
            description="Get maintenance windows for a specific service",
            content="""#!/bin/bash
if [ -z "$service_id" ]; then
    echo "Error: Service ID is required"
    exit 1
fi

curl -s \
  "https://api.pagerduty.com/maintenance_windows?service_ids[]=${service_id}&filter=ongoing" \
  -H 'Accept: application/vnd.pagerduty+json;version=2' \
  -H "Authorization: Token token=${PD_API_KEY}"
""",
            args=[
                Arg(name="service_id",
                    description="ID of the service to get maintenance windows for",
                    required=True)
            ]
        )

    def get_service_dependencies(self) -> PagerDutyTool:
        """Get technical service dependencies."""
        return PagerDutyTool(
            name="get_service_dependencies",
            description="Get technical service dependencies for a specific service",
            content="""#!/bin/bash
if [ -z "$service_id" ]; then
    echo "Error: Service ID is required"
    exit 1
fi

curl -s \
  "https://api.pagerduty.com/service_dependencies/technical_services/${service_id}" \
  -H 'Accept: application/vnd.pagerduty+json;version=2' \
  -H "Authorization: Token token=${PD_API_KEY}"
""",
            args=[
                Arg(name="service_id",
                    description="ID of the service to get dependencies for",
                    required=True)
            ]
        )

    def get_service_alerts(self) -> PagerDutyTool:
        """Get alerts for a specific service."""
        return PagerDutyTool(
            name="get_service_alerts",
            description="Get recent alerts for a specific service",
            content="""#!/bin/bash
if [ -z "$service_id" ]; then
    echo "Error: Service ID is required"
    exit 1
fi

# Handle date calculation in a portable way
if [ -z "$since" ]; then
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        since=$(date -v-7d -u +"%Y-%m-%dT%H:%M:%SZ")
    else
        # Linux and others
        since=$(date --date="-7 days" -u +"%Y-%m-%dT%H:%M:%SZ")
    fi
fi

until=${until:-$(date -u +"%Y-%m-%dT%H:%M:%SZ")}

curl -s \
  "https://api.pagerduty.com/alerts?service_ids[]=${service_id}&since=${since}&until=${until}&sort_by=created_at:desc&limit=100" \
  -H 'Accept: application/vnd.pagerduty+json;version=2' \
  -H "Authorization: Token token=${PD_API_KEY}"
""",
            args=[
                Arg(name="service_id",
                    description="ID of the service to get alerts for",
                    required=True),
                Arg(name="since",
                    description="Start date in ISO8601 format. Defaults to 7 days ago",
                    required=False),
                Arg(name="until",
                    description="End date in ISO8601 format. Defaults to current time",
                    required=False)
            ]
        )

    def get_service_statistics(self) -> PagerDutyTool:
        """Get statistics for a specific service."""
        return PagerDutyTool(
            name="get_service_statistics",
            description="Get incident statistics for a specific service",
            content="""#!/bin/bash
if [ -z "$service_id" ]; then
    echo "Error: Service ID is required"
    exit 1
fi

curl -s \
  "https://api.pagerduty.com/services/${service_id}/statistics" \
  -H 'Accept: application/vnd.pagerduty+json;version=2' \
  -H "Authorization: Token token=${PD_API_KEY}"
""",
            args=[
                Arg(name="service_id",
                    description="ID of the service to get statistics for",
                    required=True)
            ]
        )

    def list_services(self) -> PagerDutyTool:
        """List all services with optional filters."""
        return PagerDutyTool(
            name="list_services",
            description="List PagerDuty services with optional filters",
            content="""#!/bin/bash
# Build query parameters
params="time_zone=UTC&limit=100"

# Add optional filters if provided
if [ ! -z "$team_ids" ]; then
    params="${params}&team_ids[]=${team_ids}"
fi

if [ ! -z "$include" ]; then
    params="${params}&include[]=${include}"
fi

if [ ! -z "$query" ]; then
    params="${params}&query=${query}"
fi

curl -s \
  "https://api.pagerduty.com/services?${params}" \
  -H 'Accept: application/vnd.pagerduty+json;version=2' \
  -H "Authorization: Token token=${PD_API_KEY}"
""",
            args=[
                Arg(name="team_ids",
                    description="Filter by team IDs (comma-separated)",
                    required=False),
                Arg(name="include",
                    description="Include additional details (escalation_policies,teams,integrations)",
                    required=False),
                Arg(name="query",
                    description="Search query to filter services",
                    required=False)
            ]
        )

    def list_service_event_rules(self) -> PagerDutyTool:
        """List event rules for a service."""
        return PagerDutyTool(
            name="list_service_event_rules",
            description="List event rules configured for a specific service",
            content="""#!/bin/bash
if [ -z "$service_id" ]; then
    echo "Error: Service ID is required"
    exit 1
fi

curl -s \
  "https://api.pagerduty.com/services/${service_id}/rules" \
  -H 'Accept: application/vnd.pagerduty+json;version=2' \
  -H "Authorization: Token token=${PD_API_KEY}"
""",
            args=[
                Arg(name="service_id",
                    description="ID of the service to get event rules for",
                    required=True)
            ]
        )

    def list_service_change_events(self) -> PagerDutyTool:
        """List change events for a service."""
        return PagerDutyTool(
            name="list_service_change_events",
            description="List change events for a specific service",
            content="""#!/bin/bash
if [ -z "$service_id" ]; then
    echo "Error: Service ID is required"
    exit 1
fi

# Handle date calculation in a portable way
if [ -z "$since" ]; then
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        since=$(date -v-30d -u +"%Y-%m-%dT%H:%M:%SZ")
    else
        # Linux and others
        since=$(date --date="-30 days" -u +"%Y-%m-%dT%H:%M:%SZ")
    fi
fi

until=${until:-$(date -u +"%Y-%m-%dT%H:%M:%SZ")}

curl -s \
  "https://api.pagerduty.com/services/${service_id}/change_events?since=${since}&until=${until}" \
  -H 'Accept: application/vnd.pagerduty+json;version=2' \
  -H "Authorization: Token token=${PD_API_KEY}"
""",
            args=[
                Arg(name="service_id",
                    description="ID of the service to get change events for",
                    required=True),
                Arg(name="since",
                    description="Start date in ISO8601 format. Defaults to 30 days ago",
                    required=False),
                Arg(name="until",
                    description="End date in ISO8601 format. Defaults to current time",
                    required=False)
            ]
        )

    def search_services(self) -> PagerDutyTool:
        """Search for services with advanced filters."""
        return PagerDutyTool(
            name="search_services",
            description="Search for services with advanced filters",
            content="""#!/bin/bash
# Build query parameters
params="time_zone=UTC&limit=100"

if [ ! -z "$query" ]; then
    params="${params}&query=${query}"
fi

if [ ! -z "$status" ]; then
    params="${params}&status=${status}"
fi

if [ ! -z "$sort_by" ]; then
    params="${params}&sort_by=${sort_by}"
fi

curl -s \
  "https://api.pagerduty.com/services?${params}" \
  -H 'Accept: application/vnd.pagerduty+json;version=2' \
  -H "Authorization: Token token=${PD_API_KEY}"
""",
            args=[
                Arg(name="query",
                    description="Search query (e.g., service name or description)",
                    required=False),
                Arg(name="status",
                    description="Filter by status (active/disabled/maintenance)",
                    required=False),
                Arg(name="sort_by",
                    description="Sort field (name:asc/name:desc/created_at:asc/created_at:desc)",
                    required=False)
            ]
        )

    def list_service_standards(self) -> PagerDutyTool:
        """List service standards and their current status."""
        return PagerDutyTool(
            name="list_service_standards",
            description="List service standards and their current status",
            content="""#!/bin/bash
if [ -z "$service_id" ]; then
    echo "Error: Service ID is required"
    exit 1
fi

curl -s \
  "https://api.pagerduty.com/service_standards/evaluations?service_ids[]=${service_id}" \
  -H 'Accept: application/vnd.pagerduty+json;version=2' \
  -H "Authorization: Token token=${PD_API_KEY}"
""",
            args=[
                Arg(name="service_id",
                    description="ID of the service to check standards for",
                    required=True)
            ]
        )

# Initialize when module is imported
ServiceManager() 