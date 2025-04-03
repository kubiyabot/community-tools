from basic_funcs import (
    get_jira_server_url,
    get_jira_basic_headers,
    setup_client_cert_files,
    get_jira_auth,
)

import requests


def extract_relevant_fields(data):
    if not data:
        return {}
        
    fields = data.get("fields")
    if not fields:
        return {
            "issuetype_name": "N/A",
            "description_content": "N/A",
            "project_self": "N/A",
            "project_key": "N/A",
            "project_name": "N/A",
            "project_type": "N/A",
            "priority_name": "N/A",
            "created": "N/A",
            "assignee_email": "N/A",
            "assignee_displayName": "N/A",
            "reporter_email": "N/A",
            "reporter_displayName": "N/A",
            "labels": "N/A",
        }

    def safe_get(obj, *keys):
        current = obj
        for key in keys:
            if not isinstance(current, dict):
                return "N/A"
            current = current.get(key)
            if current is None:
                return "N/A"
        return current

    filtered_data = {
        "issuetype_name": safe_get(fields, "issuetype", "name"),
        "description_content": safe_get(fields, "description"),
        "project_self": safe_get(fields, "project", "self"),
        "project_key": safe_get(fields, "project", "key"),
        "project_name": safe_get(fields, "project", "name"),
        "project_type": safe_get(fields, "project", "projectTypeKey"),
        "priority_name": safe_get(fields, "priority", "name"),
        "created": safe_get(fields, "created"),
        "assignee_email": safe_get(fields, "assignee", "emailAddress"),
        "assignee_displayName": safe_get(fields, "assignee", "displayName"),
        "reporter_email": safe_get(fields, "reporter", "emailAddress"),
        "reporter_displayName": safe_get(fields, "reporter", "displayName"),
        "labels": fields.get("labels", []),
    }

    return filtered_data


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Get Jira issues")
    parser.add_argument("issue_key", help="Issue key for the Jira issue")
    args = parser.parse_args()

    cert_path, key_path = setup_client_cert_files()
    server_url = get_jira_server_url()
    auth = get_jira_auth()  # Get authentication credentials
    get_issue_url = f"{server_url}/rest/api/2/issue/{args.issue_key}"  # Changed from api/3 to api/2

    try:
        response = requests.get(
            get_issue_url, 
            headers=get_jira_basic_headers(),
            auth=auth,  # Added auth
            cert=(cert_path, key_path),
            verify=False
        )
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