import json
import requests
from typing import Dict, List

from basic_funcs import (
    get_jira_cloud_id,
    get_jira_basic_headers,
    ATLASSIAN_JIRA_API_URL,
    get_jira_user_id,
)


def get_project_issue_types(project_key: str) -> List[str]:
    """Fetch available issue types for the project"""
    cloud_id = get_jira_cloud_id()
    url = f"{ATLASSIAN_JIRA_API_URL}/{cloud_id}/rest/api/3/project/{project_key}"
    
    response = requests.get(
        url,
        headers=get_jira_basic_headers()
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
    cloud_id = get_jira_cloud_id()
    url = f"{ATLASSIAN_JIRA_API_URL}/{cloud_id}/rest/api/3/priority"
    
    response = requests.get(
        url,
        headers=get_jira_basic_headers()
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
        assignee_email: str = None,
        label: str = None,
) -> Dict:
    # Validate required fields
    if not project_key or not name or not description or not issue_type:
        raise ValueError("project_key, name, description, and issue_type are required")

    # Get available issue types for the project
    available_types = get_project_issue_types(project_key)
    if available_types:
        if issue_type not in available_types:
            raise ValueError(f"Invalid issue type '{issue_type}'. Available types are: {', '.join(available_types)}")
    
    payload = {
        "fields": {
            "project": {"key": project_key},
            "summary": name,
            "description": {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [{"text": description, "type": "text"}],
                    }
                ],
            },
            "issuetype": {"name": issue_type},
        }
    }

    # Set assignee if provided
    if assignee_email and assignee_email != "<no value>":
        try:
            user_id = get_jira_user_id(assignee_email)
            payload["fields"]["assignee"] = {"id": user_id}
        except Exception as e:
            print(f"Warning: Could not set assignee: {e}")

    # Set labels if provided
    if label and label != "<no value>":
        payload["fields"]["labels"] = [label]
    else:
        payload["fields"]["labels"] = []

    return payload


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Create Jira issue")
    parser.add_argument("project_key", help="Project key for the Jira issue")
    parser.add_argument("name", help="Summary or name of the issue")
    parser.add_argument("description", help="Description of the issue")
    parser.add_argument("issue_type", help="Type of the issue (e.g., Bug, Task)")
    parser.add_argument("--priority", help="Priority of the issue (Low, Medium, High)", default=None)
    parser.add_argument(
        "--assignee_email", help="Assignee's email address", default=None
    )
    parser.add_argument("--label", help="Label for the issue", default="")
    parser.add_argument("--parent_id", help="parent id for the task", default="")
    args = parser.parse_args()

    no_value = "<no value>"  # when no value is injected

    try:
        # Create payload
        payload = base_jira_payload(
            project_key=args.project_key,
            name=args.name,
            description=args.description,
            issue_type=args.issue_type,
            assignee_email=args.assignee_email if args.assignee_email != no_value else None,
            label=args.label if args.label != no_value else None,
        )

        # Add parent for subtasks
        if args.parent_id and args.parent_id != no_value:
            payload["fields"]["parent"] = {"key": args.parent_id}

        # Print payload for debugging
        print(f"Debug - Request payload: {json.dumps(payload, indent=2)}")

        # Get Jira cloud ID and create URL
        cloud_id = get_jira_cloud_id()
        post_issue_url = f"{ATLASSIAN_JIRA_API_URL}/{cloud_id}/rest/api/3/issue"

        # Make request
        response = requests.post(
            post_issue_url,
            headers=get_jira_basic_headers(),
            data=json.dumps(payload)
        )

        # Handle response
        if response.status_code == 201:
            print("✅ Issue created successfully.")
            print(f"Response: {json.dumps(response.json(), indent=2)}")
        else:
            error_data = response.json()
            print(f"❌ Failed to create issue. Status code: {response.status_code}")
            print(f"Error details: {json.dumps(error_data, indent=2)}")
            response.raise_for_status()

    except ValueError as e:
        print(f"❌ Validation error: {str(e)}")
        raise RuntimeError(f"Validation error: {str(e)}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {str(e)}")
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_details = e.response.json()
                print(f"Error details: {json.dumps(error_details, indent=2)}")
            except:
                print(f"Raw response: {e.response.text}")
        raise RuntimeError(f"Failed to create issue: {str(e)}")
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        raise RuntimeError(f"Failed to create issue: {str(e)}")


if __name__ == "__main__":
    main()
