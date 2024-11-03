import os

print(os.system('ls'))

import requests
import json

from basic_funcs import get_jira_cloud_id, get_jira_basic_headers, ATLASSIAN_JIRA_API_URL

cloud_id = get_jira_cloud_id()
headers = get_jira_basic_headers()

payload = {
    "fields": {
        "project": {
            "key": "{{ .project_key }}"
        },
        "summary": "{{ .name }}",
        "description": {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [
                        {
                            "text": "{{ .description }}",
                            "type": "text"
                        }
                    ]
                }
            ]
        },
        "issuetype": {
            "name": "{{ .issue_type }}"
        },
    }
}

priority, assignee_id, labels = "{{ .priority }}", "{{ .assignee_id }}", "{{ .labels }}"

if priority:
    payload["fields"]["priority"] = {
        "name": priority
    }

if assignee_id:
    payload["fields"]["assignee"] = {
        "id": assignee_id
    }

if labels:
    payload["fields"]["labels"] = labels

post_issue_url = f"{ATLASSIAN_JIRA_API_URL}/{cloud_id}/rest/api/3/issue"

try:
    response = requests.post(post_issue_url, headers=headers, data=json.dumps(payload))
    print(response.json())
except Exception as e:
    print(f"Failed to create issue: {e}")
