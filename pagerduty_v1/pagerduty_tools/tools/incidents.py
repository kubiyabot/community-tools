from typing import List
from .base import PagerDutyTool, Arg
from kubiya_sdk.tools.registry import tool_registry
import sys
import json
import os
import requests

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
                self.verify_config(),
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
            content="""
            if [ -z "$title" ] || [ -z "$urgency" ]; then
                echo "Error: Title and urgency are required"
                exit 1
            fi

            # Create incident using PagerDuty API
            curl --request POST \
                 --header "Accept: application/vnd.pagerduty+json;version=2" \
                 --header "Authorization: Token token=$PD_API_KEY" \
                 --header "Content-Type: application/json" \
                 --header "From: $KUBIYA_USER_EMAIL" \
                 --data "{
                   \\"incident\\": {
                     \\"type\\": \\"incident\\",
                     \\"title\\": \\"$title\\",
                     \\"service\\": {
                       \\"id\\": \\"$SERVICE_ID\\",
                       \\"type\\": \\"service_reference\\"
                     },
                     \\"urgency\\": \\"$urgency\\",
                     \\"body\\": {
                       \\"type\\": \\"incident_body\\",
                       \\"details\\": \\"$description\\"
                     }
                   }
                 }" \
                 "https://api.pagerduty.com/incidents"
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
            content="""
            # List incidents using PagerDuty API
            curl --request GET \
                 --header "Accept: application/vnd.pagerduty+json;version=2" \
                 --header "Authorization: Token token=$PD_API_KEY" \
                 "https://api.pagerduty.com/incidents?service_ids[]=$SERVICE_ID"
            """
        )

    def get_incident_details(self) -> PagerDutyTool:
        """Get details about a specific incident."""
        return PagerDutyTool(
            name="get_incident_details",
            description="Get detailed information about a specific incident",
            content="""
            if [ -z "$incident_id" ]; then
                echo "Error: Incident ID not specified"
                exit 1
            fi

            # Get incident details using PagerDuty API
            curl --request GET \
                 --header "Accept: application/vnd.pagerduty+json;version=2" \
                 --header "Authorization: Token token=$PD_API_KEY" \
                 "https://api.pagerduty.com/incidents/$incident_id"
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
            content="""
            if [ -z "$incident_id" ] || [ -z "$status" ]; then
                echo "Error: Incident ID and status are required"
                exit 1
            fi

            curl --request PUT \
                 --header "Accept: application/vnd.pagerduty+json;version=2" \
                 --header "Authorization: Token token=$PD_API_KEY" \
                 --header "Content-Type: application/json" \
                 --data "{
                   \\"incident\\": {
                     \\"type\\": \\"incident\\",
                     \\"status\\": \\"$status\\",
                     \\"resolution\\": \\"$resolution\\"
                   }
                 }" \
                 "https://api.pagerduty.com/incidents/$incident_id"
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
            content="""
            # List services using PagerDuty API
            curl --request GET \
                 --header "Accept: application/vnd.pagerduty+json;version=2" \
                 --header "Authorization: Token token=$PD_API_KEY" \
                 "https://api.pagerduty.com/services"
            """
        )

    def list_users(self) -> PagerDutyTool:
        """List all PagerDuty users."""
        return PagerDutyTool(
            name="list_users",
            description="List all PagerDuty users",
            content="""
            # List users using PagerDuty API
            curl --request GET \
                 --header "Accept: application/vnd.pagerduty+json;version=2" \
                 --header "Authorization: Token token=$PD_API_KEY" \
                 "https://api.pagerduty.com/users"
            """
        )

    def list_teams(self) -> PagerDutyTool:
        """List all PagerDuty teams."""
        return PagerDutyTool(
            name="list_teams",
            description="List all PagerDuty teams",
            content="""
            # List teams using PagerDuty API
            curl --request GET \
                 --header "Accept: application/vnd.pagerduty+json;version=2" \
                 --header "Authorization: Token token=$PD_API_KEY" \
                 "https://api.pagerduty.com/teams"
            """
        )

    def get_oncall_engineers(self) -> PagerDutyTool:
        """Get current on-call engineers."""
        return PagerDutyTool(
            name="get_oncall_engineers",
            description="Get the currently on-call engineers for a specific escalation policy",
            content="""
            # Set default time window to now
            current_time=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

            # Map policy name to ID
            case "$policy" in
                "Default")
                    policy_id="PAJUKLV"
                    ;;
                *)
                    echo "Error: Unknown policy name. Available options: Default"
                    exit 1
                    ;;
            esac

            # Build the URL with the policy ID
            base_url="https://api.pagerduty.com/oncalls?time_zone=UTC&since=${current_time}&until=${current_time}&escalation_policy_ids[]=${policy_id}"

            # Get on-call information using PagerDuty API
            curl --request GET \
                 --header "Accept: application/vnd.pagerduty+json;version=2" \
                 --header "Authorization: Token token=$PD_API_KEY" \
                 "${base_url}"
            """,
            args=[
                Arg(name="policy",
                    description="Name of the escalation policy (Available options: Default)",
                    required=True)
            ]
        )


# Initialize when module is imported
IncidentManager() 