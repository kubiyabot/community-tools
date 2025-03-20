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
import requests
import json
import os
import sys

def create_pd_incident():
    if not os.getenv('title') or not os.getenv('urgency'):
        print("Error: Title and urgency are required")
        sys.exit(1)

    headers = {
        'Accept': 'application/vnd.pagerduty+json;version=2',
        'Authorization': f"Token token={os.getenv('PD_API_KEY')}",
        'Content-Type': 'application/json',
        'From': os.getenv('KUBIYA_USER_EMAIL')
    }

    payload = {
        "incident": {
            "type": "incident",
            "title": os.getenv('title'),
            "service": {
                "id": os.getenv('SERVICE_ID'),
                "type": "service_reference"
            },
            "urgency": os.getenv('urgency'),
            "body": {
                "type": "incident_body",
                "details": os.getenv('description', '')
            }
        }
    }

    try:
        response = requests.post(
            'https://api.pagerduty.com/incidents',
            headers=headers,
            json=payload
        )
        
        if response.status_code == 401:
            print("Error: Authentication failed. Please check your API token permissions.")
            sys.exit(1)
        
        response.raise_for_status()
        print(json.dumps(response.json(), indent=2))
        
    except requests.exceptions.RequestException as e:
        print(f"Error creating incident: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    create_pd_incident()
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
import requests
import json
import os
import sys

def list_pd_incidents():
    headers = {
        'Accept': 'application/vnd.pagerduty+json;version=2',
        'Authorization': f"Token token={os.getenv('PD_API_KEY')}"
    }
    
    try:
        response = requests.get(
            f"https://api.pagerduty.com/incidents?service_ids[]={os.getenv('SERVICE_ID')}",
            headers=headers
        )
        response.raise_for_status()
        print(json.dumps(response.json(), indent=2))
        
    except requests.exceptions.RequestException as e:
        print(f"Error listing incidents: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    list_pd_incidents()
            """
        )

    def get_incident_details(self) -> PagerDutyTool:
        """Get details about a specific incident."""
        return PagerDutyTool(
            name="get_incident_details",
            description="Get detailed information about a specific incident",
            content="""
import requests
import json
import os
import sys

def get_pd_incident_details():
    incident_id = os.getenv('incident_id')
    if not incident_id:
        print("Error: Incident ID not specified")
        sys.exit(1)

    headers = {
        'Accept': 'application/vnd.pagerduty+json;version=2',
        'Authorization': f"Token token={os.getenv('PD_API_KEY')}"
    }
    
    try:
        response = requests.get(
            f"https://api.pagerduty.com/incidents/{incident_id}",
            headers=headers
        )
        response.raise_for_status()
        print(json.dumps(response.json(), indent=2))
        
    except requests.exceptions.RequestException as e:
        print(f"Error getting incident details: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    get_pd_incident_details()
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
import requests
import json
import os
import sys

def update_pd_incident():
    incident_id = os.getenv('incident_id')
    status = os.getenv('status')
    
    if not incident_id or not status:
        print("Error: Incident ID and status are required")
        sys.exit(1)

    headers = {
        'Accept': 'application/vnd.pagerduty+json;version=2',
        'Authorization': f"Token token={os.getenv('PD_API_KEY')}",
        'Content-Type': 'application/json'
    }

    payload = {
        "incident": {
            "type": "incident",
            "status": status,
            "resolution": os.getenv('resolution', '')
        }
    }
    
    try:
        response = requests.put(
            f"https://api.pagerduty.com/incidents/{incident_id}",
            headers=headers,
            json=payload
        )
        response.raise_for_status()
        print(json.dumps(response.json(), indent=2))
        
    except requests.exceptions.RequestException as e:
        print(f"Error updating incident: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    update_pd_incident()
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
import requests
import json
import os
import sys

def list_pd_services():
    headers = {
        'Accept': 'application/vnd.pagerduty+json;version=2',
        'Authorization': f"Token token={os.getenv('PD_API_KEY')}"
    }
    
    try:
        response = requests.get(
            "https://api.pagerduty.com/services",
            headers=headers
        )
        response.raise_for_status()
        print(json.dumps(response.json(), indent=2))
        
    except requests.exceptions.RequestException as e:
        print(f"Error listing services: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    list_pd_services()
            """
        )

    def list_users(self) -> PagerDutyTool:
        """List all PagerDuty users."""
        return PagerDutyTool(
            name="list_users",
            description="List all PagerDuty users",
            content="""
import requests
import json
import os
import sys

def list_pd_users():
    headers = {
        'Accept': 'application/vnd.pagerduty+json;version=2',
        'Authorization': f"Token token={os.getenv('PD_API_KEY')}"
    }
    
    try:
        response = requests.get(
            "https://api.pagerduty.com/users",
            headers=headers
        )
        response.raise_for_status()
        print(json.dumps(response.json(), indent=2))
        
    except requests.exceptions.RequestException as e:
        print(f"Error listing users: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    list_pd_users()
            """
        )

    def list_teams(self) -> PagerDutyTool:
        """List all PagerDuty teams."""
        return PagerDutyTool(
            name="list_teams",
            description="List all PagerDuty teams",
            content="""
import requests
import json
import os
import sys

def list_pd_teams():
    headers = {
        'Accept': 'application/vnd.pagerduty+json;version=2',
        'Authorization': f"Token token={os.getenv('PD_API_KEY')}"
    }
    
    try:
        response = requests.get(
            "https://api.pagerduty.com/teams",
            headers=headers
        )
        response.raise_for_status()
        print(json.dumps(response.json(), indent=2))
        
    except requests.exceptions.RequestException as e:
        print(f"Error listing teams: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    list_pd_teams()
            """
        )

    def get_oncall_engineers(self) -> PagerDutyTool:
        """Get current on-call engineers."""
        return PagerDutyTool(
            name="get_oncall_engineers",
            description="Get the currently on-call engineers for a specific escalation policy",
            content="""
import requests
import json
import os
import sys
from datetime import datetime

def get_pd_oncall():
    policy = os.getenv('policy')
    if not policy:
        print("Error: Policy name is required")
        sys.exit(1)

    # Map policy name to ID
    policy_mapping = {
        "Default": "PAJUKLV"
    }
    
    policy_id = policy_mapping.get(policy)
    if not policy_id:
        print("Error: Unknown policy name. Available options: Default")
        sys.exit(1)

    current_time = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    
    headers = {
        'Accept': 'application/vnd.pagerduty+json;version=2',
        'Authorization': f"Token token={os.getenv('PD_API_KEY')}"
    }
    
    try:
        response = requests.get(
            f"https://api.pagerduty.com/oncalls",
            params={
                'time_zone': 'UTC',
                'since': current_time,
                'until': current_time,
                'escalation_policy_ids[]': policy_id
            },
            headers=headers
        )
        response.raise_for_status()
        print(json.dumps(response.json(), indent=2))
        
    except requests.exceptions.RequestException as e:
        print(f"Error getting on-call engineers: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    get_pd_oncall()
            """,
            args=[
                Arg(name="policy",
                    description="Name of the escalation policy (Available options: Default)",
                    required=True)
            ]
        )


# Initialize when module is imported
IncidentManager() 