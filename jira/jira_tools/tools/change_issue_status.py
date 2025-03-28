import argparse
import json
import requests
import sys
from basic_funcs import get_jira_cloud_id, get_jira_basic_headers, ATLASSIAN_JIRA_API_URL


def get_available_transitions(issue_key):
    """Get all available transitions for a given issue"""
    jira_cloud_id = get_jira_cloud_id()
    transitions_url = f"{ATLASSIAN_JIRA_API_URL}/{jira_cloud_id}/rest/api/3/issue/{issue_key}/transitions"
    
    headers = get_jira_basic_headers()
    
    try:
        response = requests.get(transitions_url, headers=headers)
        response.raise_for_status()
        return response.json()["transitions"]
    except requests.exceptions.HTTPError as e:
        print(f"Failed to get transitions: {e}")
        sys.exit(1)


def change_issue_status(issue_key, status_name):
    """Change the status of a Jira issue"""
    jira_cloud_id = get_jira_cloud_id()
    transitions_url = f"{ATLASSIAN_JIRA_API_URL}/{jira_cloud_id}/rest/api/3/issue/{issue_key}/transitions"
    
    headers = get_jira_basic_headers()
    
    # Get available transitions
    transitions = get_available_transitions(issue_key)
    
    # Find the transition that matches the requested status name
    transition_id = None
    for transition in transitions:
        if transition["to"]["name"].lower() == status_name.lower():
            transition_id = transition["id"]
            break
    
    if not transition_id:
        available_statuses = ", ".join([t["to"]["name"] for t in transitions])
        print(f"Error: Status '{status_name}' not found. Available statuses: {available_statuses}")
        sys.exit(1)
    
    # Prepare the payload
    payload = {
        "transition": {
            "id": transition_id
        }
    }
    
    try:
        response = requests.post(transitions_url, headers=headers, data=json.dumps(payload))
        response.raise_for_status()
        print(f"Successfully changed '{issue_key}' status to '{status_name}'")
    except requests.exceptions.HTTPError as e:
        print(f"Failed to change issue status: {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description='Change the status of a Jira issue')
    parser.add_argument('issue_key', type=str, help='The Jira issue key (e.g., PROJ-123)')
    parser.add_argument('status', type=str, help='The target status (e.g., "In Progress", "Done")')
    parser.add_argument('--list-transitions', action='store_true', help='List available transitions only')
    
    args = parser.parse_args()
    
    if args.list_transitions:
        transitions = get_available_transitions(args.issue_key)
        print("Available transitions:")
        for transition in transitions:
            print(f"- {transition['to']['name']}")
    else:
        change_issue_status(args.issue_key, args.status)


if __name__ == "__main__":
    main() 