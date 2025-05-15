import json
import requests
from basic_funcs import (
    get_jira_server_url,
    get_jira_basic_headers,
    setup_client_cert_files,
    get_jira_user_id,
    get_jira_auth
)

def assign_issue(issue_key: str, assignee_email: str):
    """Assign a Jira issue to a user"""
    server_url = get_jira_server_url()
    assign_url = f"{server_url}/rest/api/2/issue/{issue_key}/assignee"
    auth = get_jira_auth()
    
    # Get user ID from email
    try:
        user_id = get_jira_user_id(assignee_email) if assignee_email else None
    except Exception as e:
        raise ValueError(f"Could not find user with email {assignee_email}: {str(e)}")
    
    # For Jira Server, use the "name" field
    if user_id:
        payload = {"name": user_id}  # For Jira Server
    else:
        # Unassign
        payload = {"name": None}
    
    cert_path, key_path = setup_client_cert_files()
    response = requests.put(
        assign_url,
        headers=get_jira_basic_headers(),
        auth=auth,
        cert=(cert_path, key_path),
        verify=False,
        data=json.dumps(payload)
    )
    response.raise_for_status()
    return True

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Assign a Jira issue to a user")
    parser.add_argument("issue_key", help="The key of the Jira issue")
    parser.add_argument("assignee_email", help="Email of the user to assign (leave empty to unassign)")
    
    args = parser.parse_args()
    
    try:
        assign_issue(args.issue_key, args.assignee_email)
        action = "unassigned" if not args.assignee_email else f"assigned to {args.assignee_email}"
        print(f"✅ Successfully {action} issue {args.issue_key}")
    except Exception as e:
        print(f"❌ Failed to assign issue: {str(e)}")
        raise RuntimeError(f"Failed to assign issue: {str(e)}")

if __name__ == "__main__":
    main() 