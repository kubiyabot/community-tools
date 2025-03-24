from basic_funcs import (
    get_jira_cloud_id,
    get_jira_basic_headers,
    ATLASSIAN_JIRA_API_URL,
)

import requests


def extract_relevant_fields(data):
    if not data:
        return {}
        
    fields = data.get("fields") or {}

    filtered_data = {
        "issuetype_name": fields.get("issuetype", {}).get("name") or "N/A",
        "description_content": fields.get("description") or "N/A",
        "project_self": fields.get("project", {}).get("self") or "N/A",
        "project_key": fields.get("project", {}).get("key") or "N/A",
        "project_name": fields.get("project", {}).get("name") or "N/A",
        "project_type": fields.get("project", {}).get("projectTypeKey") or "N/A",
        "priority_name": fields.get("priority", {}).get("name") or "N/A",
        "created": fields.get("created") or "N/A",
        "assignee_email": fields.get("assignee", {}).get("emailAddress") or "N/A",
        "assignee_displayName": fields.get("assignee", {}).get("displayName") or "N/A",
        "reporter_email": fields.get("reporter", {}).get("emailAddress") or "N/A",
        "reporter_displayName": fields.get("reporter", {}).get("displayName") or "N/A",
    }

    return filtered_data


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Get Jira issues")
    parser.add_argument("issue_key", help="Issue key for the Jira issue")
    args = parser.parse_args()
    get_issue_url = f"{ATLASSIAN_JIRA_API_URL}/{get_jira_cloud_id()}/rest/api/3/issue/{args.issue_key}"

    try:
        response = requests.get(get_issue_url, headers=get_jira_basic_headers())
        if not response.ok:
            print(f"Failed to fetch issue: HTTP {response.status_code}")
            print(f"Response: {response.text}")
            return
        
        data = response.json()
        print(extract_relevant_fields(data))
    except Exception as e:
        print(f"Failed to view issues: {e}")
        raise RuntimeError(f"Failed to view issues: {e}")


if __name__ == "__main__":
    main()
