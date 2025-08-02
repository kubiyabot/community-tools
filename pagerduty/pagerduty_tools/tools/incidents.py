from typing import List
from .base import PagerDutyTool, Arg
from kubiya_workflow_sdk.tools.registry import tool_registry
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
                self.get_oncall_engineers(),
                self.list_escalation_policies()
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
if [ -z "$title" ] || [ -z "$urgency" ] || [ -z "$service_id" ]; then
    echo "Error: Title, urgency, and service_id are required"
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
        \"id\": \"${service_id}\",
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
                Arg(name="service_id",
                    description="ID of the service to create the incident for",
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
            description="List PagerDuty incidents with optional filters (shows up to 20 most recent incidents)",
            content="""#!/bin/bash
# Install jq if not present
if ! command -v jq &> /dev/null; then
    echo "Installing jq..."
    apk add --no-cache jq
fi

# Build base query parameters
limit=20  # Fixed limit to prevent overwhelming output
offset=${offset:-0}
params="time_zone=UTC&limit=${limit}&offset=${offset}"

# Add service ID filter if provided
if [ ! -z "$service_id" ]; then
    params="${params}&service_ids[]=${service_id}"
fi

# Add status filter if provided
if [ ! -z "$status" ]; then
    params="${params}&statuses[]=${status}"
fi

# Add urgency filter if provided
if [ ! -z "$urgency" ]; then
    params="${params}&urgencies[]=${urgency}"
fi

# Add team filter if provided
if [ ! -z "$team_ids" ]; then
    params="${params}&team_ids[]=${team_ids}"
fi

# Add date range if provided
if [ ! -z "$since" ]; then
    params="${params}&since=${since}"
fi

if [ ! -z "$until" ]; then
    params="${params}&until=${until}"
fi

# Add sort parameter if provided
sort_by=${sort_by:-"created_at:desc"}
params="${params}&sort_by=${sort_by}"

# Make the API call
response=$(curl -s \
  "https://api.pagerduty.com/incidents?${params}" \
  -H 'Accept: application/vnd.pagerduty+json;version=2' \
  -H "Authorization: Token token=${PD_API_KEY}")

# Extract pagination information
total=$(echo "$response" | grep -o '"total":[0-9]*' | cut -d':' -f2)

# Display summary header
echo "=== PagerDuty Incidents ==="
if [ ! -z "$total" ] && [ "$total" -gt "$limit" ]; then
    echo "Showing ${limit} most recent incidents out of ${total} total incidents"
    echo "Use --offset parameter to view more incidents"
else
    echo "Found ${total:-0} incidents"
fi
echo "----------------------------------------"
echo

# Process and format the incidents for better readability
echo "$response" | jq -r '
  .incidents[] | 
  "=== Incident #\(.incident_number) ===\n" +
  "Title: \(.title)\n" +
  "Status: \(.status)\n" +
  "Urgency: \(.urgency)\n" +
  "Created: \(.created_at)\n" +
  "Service: \(.service.summary)\n" +
  (if .assigned_to then "Assigned to: \(.assigned_to[].summary)" else "Assigned to: Unassigned" end) +
  "\nURL: \(.html_url)\n"
'

# If there are more incidents, show a footer message
if [ ! -z "$total" ] && [ "$total" -gt "$limit" ]; then
    echo "----------------------------------------"
    remaining=$((total - limit))
    echo "There are ${remaining} more incidents available."
    echo "Use --offset ${limit} to see the next page of results."
fi
""",
            args=[
                Arg(name="offset",
                    description="Number of incidents to skip (for viewing older incidents)",
                    required=False),
                Arg(name="service_id",
                    description="Filter by service ID",
                    required=False),
                Arg(name="status",
                    description="Filter by status (triggered/acknowledged/resolved)",
                    required=False),
                Arg(name="urgency",
                    description="Filter by urgency (high/low)",
                    required=False),
                Arg(name="team_ids",
                    description="Filter by team IDs (comma-separated)",
                    required=False),
                Arg(name="since",
                    description="Start date in ISO8601 format (e.g., 2023-01-01T00:00:00Z)",
                    required=False),
                Arg(name="until",
                    description="End date in ISO8601 format (e.g., 2023-12-31T23:59:59Z)",
                    required=False),
                Arg(name="sort_by",
                    description="Sort field (created_at:asc/created_at:desc/resolved_at:asc/resolved_at:desc/urgency:asc/urgency:desc)",
                    required=False)
            ]
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

    def list_escalation_policies(self) -> PagerDutyTool:
        """List all PagerDuty escalation policies."""
        return PagerDutyTool(
            name="list_escalation_policies",
            description="List all available PagerDuty escalation policies",
            content="""#!/bin/bash
# Install jq if not present
if ! command -v jq &> /dev/null; then
    echo "Installing jq..."
    apk add --no-cache jq
fi

response=$(curl -s \
  'https://api.pagerduty.com/escalation_policies' \
  -H 'Accept: application/vnd.pagerduty+json;version=2' \
  -H "Authorization: Token token=${PD_API_KEY}")

echo "=== PagerDuty Escalation Policies ==="
echo "$response" | jq -r '.escalation_policies[] | "ID: \(.id)\nName: \(.name)\nDescription: \(.description // "No description")\n---"'
"""
        )

# Initialize when module is imported
IncidentManager() 