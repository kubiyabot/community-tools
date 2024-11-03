from basic_funcs import get_jira_cloud_id, get_jira_basic_headers, get_jira_user_id, ATLASSIAN_JIRA_API_URL

import argparse
import json
import requests

def create_jira_payload(project_key, name, description, issue_type, priority=None, assignee_email=None, label=None):
    payload = {
        "fields": {
            "project": {"key": project_key},
            "summary": name,
            "description": {
                "type": "doc",
                "version": 1,
                "content": [{
                    "type": "paragraph",
                    "content": [{
                        "text": description,
                        "type": "text"
                    }]
                }]
            },
            "issuetype": {"name": issue_type}
        }
    }

    if priority:
        payload["fields"]["priority"] = {"name": priority}
    if assignee_email:
        payload["fields"]["assignee"] = {"id": get_jira_user_id(assignee_email)}
    if label:
        payload["fields"]["labels"] = [label]

    return payload

def main():
    parser = argparse.ArgumentParser(description="Create Jira issue")
    parser.add_argument("project_key", help="Project key for the Jira issue")
    parser.add_argument("name", help="Summary or name of the issue")
    parser.add_argument("description", help="Description of the issue")
    parser.add_argument("issue_type", help="Type of the issue (e.g., Bug, Task)")
    parser.add_argument("--priority", help="Priority of the issue", default=None)
    parser.add_argument("--assignee_email", help="Assignee's email address", default=None)
    parser.add_argument("--label", help="Label for the issue", default=None)
    args = parser.parse_args()

    cloud_id = get_jira_cloud_id()
    headers = get_jira_basic_headers()
    payload = create_jira_payload(
        project_key=args.project_key,
        name=args.name,
        description=args.description,
        issue_type=args.issue_type,
        priority=args.priority,
        assignee_email=args.assignee_email,
        label=args.label
    )

    post_issue_url = f"{ATLASSIAN_JIRA_API_URL}/{cloud_id}/rest/api/3/issue"

    try:
        response = requests.post(post_issue_url, headers=headers, data=json.dumps(payload))
        print(response.json())
    except Exception as e:
        print(f"Failed to create issue: {e}")

if __name__ == "__main__":
    main()
