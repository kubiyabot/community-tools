import argparse
import os

print(os.system('ls'))

import requests
import json

from basic_funcs import get_jira_cloud_id, get_jira_basic_headers, ATLASSIAN_JIRA_API_URL

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="create jira issue")
    parser.add_argument("project_key")
    parser.add_argument("name")
    parser.add_argument("description")
    parser.add_argument("issue_type")
    parser.add_argument("priority")
    parser.add_argument("assignee_id")
    args = parser.parse_args()

    project_key, name, description, issue_type, priority, assignee_id = args.project_key, args.name, args.description, args.issue_type, args.priority, args.assignee_id

    cloud_id = get_jira_cloud_id()
    headers = get_jira_basic_headers()

    print("hi hi {{ .project_key }}")
    payload = {
        "fields": {
            "project": {
                "key": project_key
            },
            "summary": name,
            "description": {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [
                            {
                                "text": description,
                                "type": "text"
                            }
                        ]
                    }
                ]
            },
            "issuetype": {
                "name": issue_type
            },
        }
    }

    if priority:
        payload["fields"]["priority"] = {
            "name": priority
        }

    if assignee_id:
        payload["fields"]["assignee"] = {
            "id": assignee_id
        }

    # if labels:
    #     payload["fields"]["labels"] = labels

    post_issue_url = f"{ATLASSIAN_JIRA_API_URL}/{cloud_id}/rest/api/3/issue"

    try:
        response = requests.post(post_issue_url, headers=headers, data=json.dumps(payload))
        print(response.json())
    except Exception as e:
        print(f"Failed to create issue: {e}")

