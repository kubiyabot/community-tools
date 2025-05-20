import json
import requests
from typing import Dict, List
import os

from basic_funcs import (
    get_jira_server_url,
    get_jira_basic_headers,
    setup_client_cert_files,
    get_jira_user_id,
    get_jira_auth,
    test_jira_connection,
)
import urllib3

# Suppress only the specific InsecureRequestWarning
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def get_project_issue_types(project_key: str) -> List[str]:
    """Fetch available issue types for the project"""
    # Test connection first
    if not test_jira_connection():
        print("Failed to establish connection to Jira. Please check your configuration.")
        return []
        
    server_url = get_jira_server_url()
    url = f"{server_url}/rest/api/2/project/{project_key}"  # Changed from api/3 to api/2
    cert_path, key_path = setup_client_cert_files()
    auth = get_jira_auth()
    headers = get_jira_basic_headers()
    
    response = requests.get(
        url,
        headers=headers,
        auth=auth,
        cert=(cert_path, key_path),
        verify=False  # Often needed for self-hosted instances
    )
    
    if response.status_code == 200:
        project_data = response.json()
        issue_types = [it['name'] for it in project_data.get('issueTypes', [])]
        print(f"Available issue types for project {project_key}: {issue_types}")
        return issue_types
    else:
        print(f"Failed to fetch project issue types. Status code: {response.status_code}")
        print(f"Error details: {response.text}")
        return []

def get_priority_id(priority_name: str) -> str:
    """Get priority ID from priority name"""
    server_url = get_jira_server_url()
    url = f"{server_url}/rest/api/2/priority"  # Changed from api/3 to api/2
    cert_path, key_path = setup_client_cert_files()
    auth = get_jira_auth()
    headers = get_jira_basic_headers()
    
    response = requests.get(
        url,
        headers=headers,
        auth=auth,
        cert=(cert_path, key_path),
        verify=False
    )
    
    if response.status_code == 200:
        priorities = response.json()
        for p in priorities:
            if p['name'].lower() == priority_name.lower():
                return p['id']
        print(f"Warning: Priority '{priority_name}' not found in available priorities")
        return None
    else:
        print(f"Failed to fetch priorities. Status code: {response.status_code}")
        return None

def base_jira_payload(
        project_key: str,
        name: str,
        description: str,
        issue_type: str,
        assignee_name: str = None,
        label: str = None,
        priority: str = None,
        component: str = None,
) -> Dict:
    # Validate required fields
    if not project_key or not name or not issue_type:
        raise ValueError("project_key, name, and issue_type are required")

    # Get available issue types for the project
    available_types = get_project_issue_types(project_key)
    if available_types:
        if issue_type not in available_types:
            raise ValueError(f"Invalid issue type '{issue_type}'. Available types are: {', '.join(available_types)}")
    
    # Simplified payload format for Jira Server
    payload = {
        "fields": {
            "project": {"key": project_key},
            "summary": name,
            "issuetype": {"name": issue_type},
        }
    }

    # Add description if provided
    if description:
        payload["fields"]["description"] = description

    # Set assignee if provided
    if assignee_name and assignee_name != "<no value>":
        try:
            # For Jira Server, we should use name instead of id
            payload["fields"]["assignee"] = {"name": assignee_name}
        except Exception as e:
            print(f"Warning: Could not set assignee: {e}")

    # Set labels if provided
    if label and label != "<no value>":
        payload["fields"]["labels"] = [l.strip() for l in label.split(",")]
    else:
        payload["fields"]["labels"] = []
        
    # Set priority if provided
    if priority and priority != "<no value>":
        priority_id = get_priority_id(priority)
        if priority_id:
            payload["fields"]["priority"] = {"id": priority_id}
    
    # Always set component to "Kubika-O" regardless of input
    payload["fields"]["components"] = [{"name": "Kubika-O"}]
    
    return payload

def create_issue(project_key: str, summary: str, description: str, issue_type: str, 
                assignee_email: str = None, label: str = None, 
                parent_id: str = None, priority: str = None, component: str = None):
    """
    Create a Jira issue with the given parameters.
    If assignee_email is provided, it will be converted to a Jira username.
    If no assignee_email is provided, it will use KUBIYA_USER_EMAIL environment variable.
    """
    # Test connection first
    if not test_jira_connection():
        print("Failed to establish connection to Jira. Please check your configuration.")
        return False
    
    # Initialize assignee_name to None
    assignee_name = None
    
    # If assignee_email is provided, convert it to a username
    if assignee_email and assignee_email != "<no value>":
        try:
            assignee_name = get_jira_user_id(assignee_email)
            print(f"✅ Found Jira user: {assignee_name} for email: {assignee_email}")
        except Exception as e:
            print(f"⚠️ Could not find Jira user for email {assignee_email}: {str(e)}")
            print("Will try to use current user instead.")
    
    # If no assignee is specified or the provided email couldn't be found, use the current user
    if not assignee_name:
        user_email = os.environ.get("KUBIYA_USER_EMAIL")
        if user_email:
            try:
                assignee_name = get_jira_user_id(user_email)
                print(f"✅ Using current user as assignee: {assignee_name} (from email: {user_email})")
            except Exception as e:
                print(f"⚠️ Could not find Jira user for current user email {user_email}: {str(e)}")
                print("Issue will be created without an assignee.")
    
    server_url = get_jira_server_url()
    issue_url = f"{server_url}/rest/api/2/issue"
    cert_path, key_path = setup_client_cert_files()
    auth = get_jira_auth()
    headers = get_jira_basic_headers()

    try:
        # Create payload - note that component parameter is still passed but will be ignored
        payload = base_jira_payload(
            project_key=project_key,
            name=summary,
            description=description,
            issue_type=issue_type,
            assignee_name=assignee_name,
            label=label,
            priority=priority,
            component=component,  # This will be ignored as we hardcode to "Kubika-O"
        )

        # Add parent for subtasks
        if parent_id and parent_id != "<no value>":
            payload["fields"]["parent"] = {"key": parent_id}

        # Print payload for debugging
        print(f"Debug - Request payload: {json.dumps(payload, indent=2)}")

        # Make request
        response = requests.post(
            issue_url,
            headers=headers,
            auth=auth,
            cert=(cert_path, key_path),
            verify=False,
            data=json.dumps(payload)
        )
        
        if response.status_code == 403:
            if 'X-Authentication-Denied-Reason' in response.headers:
                if 'CAPTCHA_CHALLENGE' in response.headers['X-Authentication-Denied-Reason']:
                    print("CAPTCHA verification required. Please log in through the web interface first.")
                    print("URL:", response.headers.get('X-Authentication-Denied-Reason').split('login-url=')[1])
                    return False
            
        if response.status_code == 401:
            print("Authentication failed. Please check your credentials and certificates.")
            return False

        # Handle response
        if response.status_code == 201:
            response_data = response.json()
            issue_key = response_data.get('key')
            print(f"✅ Issue created successfully: {issue_key}")
            print(f"Response: {json.dumps(response_data, indent=2)}")
            return issue_key
        else:
            error_data = response.json()
            print(f"❌ Failed to create issue. Status code: {response.status_code}")
            print(f"Error details: {json.dumps(error_data, indent=2)}")
            response.raise_for_status()
            return False

    except ValueError as e:
        print(f"❌ Validation error: {str(e)}")
        raise RuntimeError(f"Validation error: {str(e)}")
    except requests.exceptions.SSLError as e:
        print("\nSSL Error occurred. Please check your certificates.")
        print(str(e))
        return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {str(e)}")
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_details = e.response.json()
                print(f"Error details: {json.dumps(error_details, indent=2)}")
            except:
                print(f"Raw response: {e.response.text}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        return False

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Create Jira issue")
    parser.add_argument("project_key", help="Project key for the Jira issue")
    parser.add_argument("name", help="Summary or name of the issue")
    parser.add_argument("description", help="Description of the issue")
    parser.add_argument("issue_type", help="Type of the issue (e.g., Bug, Task)")
    parser.add_argument("--priority", help="Priority of the issue (Low, Medium, High, Major)", default=None)
    parser.add_argument("--assignee_email", help="Email of user to assign the issue to (defaults to current user if not specified)", default=None)
    parser.add_argument("--label", help="Label for the issue", default="")
    parser.add_argument("--parent_id", help="parent id for the task", default="")
    parser.add_argument("--component", help="Component for the issue", default="")
    args = parser.parse_args()

    no_value = "<no value>"  # when no value is injected

    result = create_issue(
        project_key=args.project_key,
        summary=args.name,
        description=args.description,
        issue_type=args.issue_type,
        assignee_email=args.assignee_email if args.assignee_email != no_value else None,
        label=args.label if args.label != no_value else None,
        parent_id=args.parent_id if args.parent_id != no_value else None,
        priority=args.priority if args.priority != no_value else None,
        component=args.component if args.component != no_value else None
    )
    
    if not result:
        raise RuntimeError(f"Failed to create issue")
    
    return result

if __name__ == "__main__":
    main() 