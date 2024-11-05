from basic_funcs import (
    get_jira_cloud_id,
    get_jira_basic_headers,
    ATLASSIAN_JIRA_API_URL,
)

import requests


def extract_relevant_fields(data):
    fields = data.get("fields", {})

    filtered_data = {
        "issuetype_name": fields.get("issuetype", {}).get("name", None),
        "description_content": fields.get("description", {}),
        "project_self": fields.get("project", {}).get("self", None),
        "project_key": fields.get("project", {}).get("key", None),
        "project_name": fields.get("project", {}).get("name", None),
        "project_type": fields.get("project", {}).get("projectTypeKey", None),
        "priority_name": fields.get("priority", {}).get("name", None),
        "created": fields.get("created", None),
        "assignee_email": fields.get("assignee", {}).get("emailAddress", None),
        "assignee_displayName": fields.get("assignee", {}).get("displayName", None),
        "reporter_email": fields.get("reporter", {}).get("emailAddress", None),
        "reporter_displayName": fields.get("reporter", {}).get("displayName", None),
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
        print(extract_relevant_fields(response.json()))
    except Exception as e:
        print(f"Failed to view issues: {e}")
        raise RuntimeError(f"Failed to view issues: {e}")


if __name__ == "__main__":
    main()
