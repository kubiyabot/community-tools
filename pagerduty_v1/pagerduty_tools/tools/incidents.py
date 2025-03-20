from typing import List
from .base import PagerDutyTool, Arg
from kubiya_sdk.tools.registry import tool_registry
import sys

class IncidentManager:
    """Manage PagerDuty incidents."""
    
    def __init__(self):
        """Initialize and register all tools."""
        try:
            # Register all tools
            tools = [
                self.create_incident(),
                self.list_incidents(),
                self.get_incident_details(),
                self.update_incident(),
                self.list_services(),
                self.list_users(),
                self.list_teams(),
                self.get_oncall_engineers()
            ]
            
            for tool in tools:
                try:
                    tool_registry.register("pagerduty", tool)
                    print(f"✅ Registered: {tool.name}")
                except Exception as e:
                    print(f"❌ Failed to register {tool.name}: {str(e)}", file=sys.stderr)
                    raise

        except Exception as e:
            print(f"❌ Failed to register PagerDuty tools: {str(e)}", file=sys.stderr)
            raise

    def create_incident(self) -> PagerDutyTool:
        """Create a new PagerDuty incident."""
        return PagerDutyTool(
            name="create_incident",
            description="Create a new PagerDuty incident",
            content="""#!/bin/bash
if [ -z "$title" ] || [ -z "$urgency" ]; then
    echo "Error: Title and urgency are required"
    exit 1
fi

description=${description:-""}

curl -s -X POST \
  'https://api.pagerduty.com/incidents' \
  -H 'Accept: application/vnd.pagerduty+json;version=2' \
  -H "Authorization: Token token=${PD_API_KEY}" \
  -H 'Content-Type: application/json' \
  -H "From: ${KUBIYA_USER_EMAIL}" \
  -d "{
    \"incident\": {
      \"type\": \"incident\",
      \"title\": \"${title}\",
      \"service\": {
        \"id\": \"${SERVICE_ID}\",
        \"type\": \"service_reference\"
      },
      \"urgency\": \"${urgency}\",
      \"body\": {
        \"type\": \"incident_body\",
        \"details\": \"${description}\"
      }
    }
  }"
""",
            args=[
                Arg(name="title",
                    description="Title of the incident",
                    required=True),
                Arg(name="urgency",
                    description="Incident urgency (high/low)",
                    required=True),
                Arg(name="description",
                    description="Detailed description of the incident",
                    required=False)
            ]
        )

    def list_incidents(self) -> PagerDutyTool:
        """List PagerDuty incidents."""
        return PagerDutyTool(
            name="list_incidents",
            description="List PagerDuty incidents",
            content="""#!/bin/bash
curl -s \
  "https://api.pagerduty.com/incidents?service_ids[]=${SERVICE_ID}" \
  -H 'Accept: application/vnd.pagerduty+json;version=2' \
  -H "Authorization: Token token=${PD_API_KEY}"
"""
        )

    def get_incident_details(self) -> PagerDutyTool:
        """Get details about a specific incident."""
        return PagerDutyTool(
            name="get_incident_details",
            description="Get detailed information about a specific incident",
            content="""#!/bin/bash
if [ -z "$incident_id" ]; then
    echo "Error: Incident ID not specified"
    exit 1
fi

curl -s \
  "https://api.pagerduty.com/incidents/${incident_id}" \
  -H 'Accept: application/vnd.pagerduty+json;version=2' \
  -H "Authorization: Token token=${PD_API_KEY}"
""",
            args=[
                Arg(name="incident_id",
                    description="ID of the incident",
                    required=True)
            ]
        )

    def update_incident(self) -> PagerDutyTool:
        """Update an incident's status."""
        return PagerDutyTool(
            name="update_incident",
            description="Update an incident's status",
            content="""#!/bin/bash
if [ -z "$incident_id" ] || [ -z "$status" ]; then
    echo "Error: Incident ID and status are required"
    exit 1
fi

resolution=${resolution:-""}

curl -s -X PUT \
  "https://api.pagerduty.com/incidents/${incident_id}" \
  -H 'Accept: application/vnd.pagerduty+json;version=2' \
  -H "Authorization: Token token=${PD_API_KEY}" \
  -H 'Content-Type: application/json' \
  -d "{
    \"incident\": {
      \"type\": \"incident\",
      \"status\": \"${status}\",
      \"resolution\": \"${resolution}\"
    }
  }"
""",
            args=[
                Arg(name="incident_id",
                    description="ID of the incident",
                    required=True),
                Arg(name="status",
                    description="New status (resolved/acknowledged)",
                    required=True),
                Arg(name="resolution",
                    description="Resolution notes",
                    required=False)
            ]
        )

    def list_services(self) -> PagerDutyTool:
        """List all PagerDuty services."""
        return PagerDutyTool(
            name="list_services",
            description="List all available PagerDuty services",
            content="""#!/bin/bash
curl -s \
  'https://api.pagerduty.com/services' \
  -H 'Accept: application/vnd.pagerduty+json;version=2' \
  -H "Authorization: Token token=${PD_API_KEY}"
"""
        )

    def list_users(self) -> PagerDutyTool:
        """List all PagerDuty users."""
        return PagerDutyTool(
            name="list_users",
            description="List all PagerDuty users",
            content="""#!/bin/bash
curl -s \
  'https://api.pagerduty.com/users' \
  -H 'Accept: application/vnd.pagerduty+json;version=2' \
  -H "Authorization: Token token=${PD_API_KEY}"
"""
        )

    def list_teams(self) -> PagerDutyTool:
        """List all PagerDuty teams."""
        return PagerDutyTool(
            name="list_teams",
            description="List all PagerDuty teams",
            content="""#!/bin/bash
curl -s \
  'https://api.pagerduty.com/teams' \
  -H 'Accept: application/vnd.pagerduty+json;version=2' \
  -H "Authorization: Token token=${PD_API_KEY}"
"""
        )

    def get_oncall_engineers(self) -> PagerDutyTool:
        """Get current on-call engineers."""
        return PagerDutyTool(
            name="get_oncall_engineers", 
            description="Get the currently on-call engineers for a specific escalation policy",
            content="""#!/bin/bash
if [ -z "$policy" ]; then
    echo "Error: Policy name is required"
    exit 1
fi

# First, get the policy ID by searching through escalation policies
policy_id=$(curl -s \
  "https://api.pagerduty.com/escalation_policies?query=${policy}" \
  -H 'Accept: application/vnd.pagerduty+json;version=2' \
  -H "Authorization: Token token=${PD_API_KEY}" \
  | grep -o '"id":"[^"]*' | head -1 | cut -d'"' -f4)

if [ -z "$policy_id" ]; then
    echo "Error: Could not find escalation policy with name: ${policy}"
    exit 1
fi

current_time=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

curl -s \
  "https://api.pagerduty.com/oncalls?time_zone=UTC&since=${current_time}&until=${current_time}&escalation_policy_ids[]=${policy_id}" \
  -H 'Accept: application/vnd.pagerduty+json;version=2' \
  -H "Authorization: Token token=${PD_API_KEY}"
""",
            args=[
                Arg(name="policy",
                    description="Name of the escalation policy to search for",
                    required=True)
            ]
        )


# Initialize when module is imported
IncidentManager() 