import json
import requests
from basic_funcs import (
    get_jira_server_url,
    get_jira_basic_headers,
    setup_client_cert_files,
)

def get_available_transitions(issue_key: str):
    server_url = get_jira_server_url()
    transitions_url = f"{server_url}/rest/api/3/issue/{issue_key}/transitions"
    cert_path, key_path = setup_client_cert_files()
    
    response = requests.get(
        transitions_url,
        headers=get_jira_basic_headers(),
        cert=(cert_path, key_path),
        verify=False
    )
    response.raise_for_status()
    return response.json()['transitions']

def update_issue_status(issue_key: str, status_name: str):
    # Get available transitions
    transitions = get_available_transitions(issue_key)
    
    # Find matching transition
    transition_id = None
    for transition in transitions:
        if transition['name'].lower() == status_name.lower():
            transition_id = transition['id']
            break
    
    if not transition_id:
        available_statuses = [t['name'] for t in transitions]
        raise ValueError(f"Status '{status_name}' not found. Available statuses: {', '.join(available_statuses)}")
    
    # Perform transition
    server_url = get_jira_server_url()
    transition_url = f"{server_url}/rest/api/3/issue/{issue_key}/transitions"
    cert_path, key_path = setup_client_cert_files()
    
    payload = {
        "transition": {
            "id": transition_id
        }
    }
    
    response = requests.post(
        transition_url,
        headers=get_jira_basic_headers(),
        cert=(cert_path, key_path),
        verify=False,
        data=json.dumps(payload)
    )
    response.raise_for_status()
    return True

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Update Jira issue status")
    parser.add_argument("issue_key", help="Issue key for the Jira issue")
    parser.add_argument("status", help="New status for the issue")
    
    args = parser.parse_args()
    
    try:
        update_issue_status(args.issue_key, args.status)
        print(f"✅ Successfully updated {args.issue_key} status to '{args.status}'")
    except Exception as e:
        print(f"❌ Failed to update issue status: {str(e)}")
        raise RuntimeError(f"Failed to update issue status: {str(e)}")

if __name__ == "__main__":
    main() 