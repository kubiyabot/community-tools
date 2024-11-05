import json
import requests
from typing import Dict

from basic_funcs import (
    get_jira_cloud_id,
    get_jira_basic_headers,
    ATLASSIAN_JIRA_API_URL,
    get_jira_user_id,
)


def base_jira_payload(
        project_key: str,
        name: str,
        description: str,
        issue_type: str,
        priority: str = None,
        assignee_email: str = None,
        label: str = None,
) -> Dict:
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

    if priority:
        payload["fields"]["priority"] = {"name": priority}

    if assignee_email:
        payload["fields"]["assignee"] = {"id": get_jira_user_id(assignee_email)}

    payload["fields"]["labels"] = [label] if label else [""]

    return payload


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Create Jira issue")
    parser.add_argument("project_key", help="Project key for the Jira issue")
    parser.add_argument("name", help="Summary or name of the issue")
    parser.add_argument("description", help="Description of the issue")
    parser.add_argument("issue_type", help="Type of the issue (e.g., Bug, Task)")
    parser.add_argument("--priority", help="Priority of the issue", default=None)
    parser.add_argument(
        "--assignee_email", help="Assignee's email address", default=None
    )
    parser.add_argument("--label", help="Label for the issue", default="")
    parser.add_argument("--parent_id", help="parent id for the task", default="")
    args = parser.parse_args()

    no_value = "<no value>"  # when no value is injected

    payload = base_jira_payload(
        project_key=args.project_key,
        name=args.name,
        description=args.description,
        issue_type=args.issue_type,
        priority=args.priority if args.priority != no_value else None,
        assignee_email=args.assignee_email if args.assignee_email != no_value else None,
        label=args.label if args.label != no_value else None,
    )

    if args.parent_id:  # especially for subtasks
        payload["fields"]["parent"] = {"key": args.parent_id}

    post_issue_url = f"{ATLASSIAN_JIRA_API_URL}/{get_jira_cloud_id()}/rest/api/3/issue"

    try:
        response = requests.post(
            post_issue_url, headers=get_jira_basic_headers(), data=json.dumps(payload)
        )
        response.raise_for_status()
        print(response.json())
        print("Issue created successfully.")
    except Exception as e:
        print(f"Failed to create issue: {e}")
        raise RuntimeError(f"Failed to create issue: {e}")


if __name__ == "__main__":
    main()
