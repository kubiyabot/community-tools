from basic_funcs import (
    get_jira_cloud_id,
    get_jira_basic_headers,
    ATLASSIAN_JIRA_API_URL,
)

import requests


def get_or_default(dictionary, *keys, default=None):
    for key in keys:
        dictionary = dictionary.get(key)
        if dictionary is None:
            return default
    return dictionary

def extract_relevant_fields(data):
    fields = data.get("fields", {})

    filtered_data = {
        "issuetype_name": get_or_default(fields, "issuetype", "name"),
        "description_content": get_or_default(fields, "description"),
        "project_self": get_or_default(fields, "project", "self"),
        "project_key": get_or_default(fields, "project", "key"),
        "project_name": get_or_default(fields, "project", "name"),
        "project_type": get_or_default(fields, "project", "projectTypeKey"),
        "priority_name": get_or_default(fields, "priority", "name"),
        "created": get_or_default(fields, "created"),
        "assignee_email": get_or_default(fields, "assignee", "emailAddress"),
        "assignee_displayName": get_or_default(fields, "assignee", "displayName"),
        "reporter_email": get_or_default(fields, "reporter", "emailAddress"),
        "reporter_displayName": get_or_default(fields, "reporter", "displayName"),
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
