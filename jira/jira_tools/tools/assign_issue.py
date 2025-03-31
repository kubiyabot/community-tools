import json
import requests
from basic_funcs import (
    get_jira_cloud_id,
    get_jira_basic_headers,
    ATLASSIAN_JIRA_API_URL,
    get_jira_user_id
)

def assign_issue(issue_key: str, assignee_email: str):
    """Assign a Jira issue to a user"""
    cloud_id = get_jira_cloud_id()
    assign_url = f"{ATLASSIAN_JIRA_API_URL}/{cloud_id}/rest/api/3/issue/{issue_key}/assignee"
    
    # Get user ID from email
    try:
        user_id = get_jira_user_id(assignee_email) if assignee_email else None
    except Exception as e:
        raise ValueError(f"Could not find user with email {assignee_email}: {str(e)}")
    
    payload = {
        "accountId": user_id
    } if user_id else {"accountId": None}  # None to unassign
    
    response = requests.put(
        assign_url,
        headers=get_jira_basic_headers(),
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