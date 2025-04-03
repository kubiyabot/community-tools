import json
import requests
from basic_funcs import (
    get_jira_server_url,
    get_jira_basic_headers,
    setup_client_cert_files,
    get_jira_auth,
)

def list_projects():
    """List all accessible Jira projects"""
    server_url = get_jira_server_url()
    projects_url = f"{server_url}/rest/api/2/project"
    cert_path, key_path = setup_client_cert_files()
    auth = get_jira_auth()

    try:
        response = requests.get(
            projects_url,
            headers=get_jira_basic_headers(),
            auth=auth,
            cert=(cert_path, key_path),
            verify=False
        )
        response.raise_for_status()
        
        projects = response.json()
        return [{
            "key": project["key"],
            "name": project["name"],
            "id": project["id"],
            "projectTypeKey": project.get("projectTypeKey", "N/A"),
            "style": project.get("style", "N/A"),
        } for project in projects]

    except Exception as e:
        print(f"Failed to list projects: {str(e)}")
        raise RuntimeError(f"Failed to list projects: {str(e)}")

def main():
    try:
        projects = list_projects()
        print("\nAvailable Jira Projects:")
        print("------------------------")
        for project in projects:
            print(f"Key: {project['key']}")
            print(f"Name: {project['name']}")
            print(f"ID: {project['id']}")
            print(f"Type: {project['projectTypeKey']}")
            print(f"Style: {project['style']}")
            print("------------------------")
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        raise RuntimeError(str(e))

if __name__ == "__main__":
    main() 