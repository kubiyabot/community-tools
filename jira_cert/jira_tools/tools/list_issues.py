from typing import List

from basic_funcs import (
    get_jira_server_url,
    get_jira_basic_headers,
    setup_client_cert_files,
)

import requests


def list_issues_in_project(
    project_key: str,
    num_issues: int = 5,
    status: str = None,
    assignee: str = None,
    priority: str = None,
    reporter: str = None,
    label: str = None,
)-> List[dict]:

    jql_query = f"project = {project_key}"
    if status:
        jql_query += f" AND status = '{status}'"
    if assignee:
        jql_query += f" AND assignee = '{assignee}'"
    if priority:
        jql_query += f" AND priority = '{priority}'"
    if reporter:
        jql_query += f" AND reporter = '{reporter}'"
    if label:
        jql_query += f" AND labels = '{label}'"

    params = {
        "jql": jql_query,
        "maxResults": num_issues,
        "fields": "summary,created,labels",
    }
    try:
        server_url = get_jira_server_url()
        search_url = f"{server_url}/rest/api/3/search"
        cert_path, key_path = setup_client_cert_files()
        
        response = requests.get(
            search_url, 
            headers=get_jira_basic_headers(), 
            params=params,
            cert=(cert_path, key_path),
            verify=False
        )
        response.raise_for_status()

        issues = response.json().get("issues", [])
        latest_issues = [
            {
                "key": issue["key"],
                "summary": issue["fields"]["summary"],
                "created": issue["fields"]["created"],
                "labels": issue["fields"].get("labels", []),
            }
            for issue in issues
        ]

        return latest_issues

    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return []


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="List Jira issues")
    parser.add_argument("project_key", help="Jira project key")
    parser.add_argument("issues_number", nargs='?', type=str, help="Number of issues to list")
    parser.add_argument("status", nargs='?', type=str, help="Issues status, such as Done")
    parser.add_argument("assignee", nargs='?', type=str, help="Including assignee user")
    parser.add_argument("priority", nargs='?', type=str, help="Including issues priority")
    parser.add_argument("reporter", nargs='?', type=str, help="Including assignee reporter")
    parser.add_argument("label", nargs='?', type=str, help="Filter by label")
    
    args = parser.parse_args()

    try:
        # Handle '<no value>' as None
        issues_number = args.issues_number if args.issues_number and args.issues_number != '<no value>' else None
        status = args.status if args.status and args.status != '<no value>' else None
        assignee = args.assignee if args.assignee and args.assignee != '<no value>' else None
        priority = args.priority if args.priority and args.priority != '<no value>' else None
        reporter = args.reporter if args.reporter and args.reporter != '<no value>' else None
        label = args.label if args.label and args.label != '<no value>' else None

        # Convert issues_number to int if present, otherwise use default
        issues_number = int(issues_number) if issues_number else 5

        latest_issues = list_issues_in_project(
            args.project_key,
            issues_number,
            status,
            assignee,
            priority,
            reporter,
            label,
        )
        for issue in latest_issues:
            labels_str = f" - Labels: {', '.join(issue['labels'])}" if issue['labels'] else ""
            print(
                f"{issue['key']}: {issue['summary']} - Created on {issue['created']}{labels_str}"
            )

    except ValueError as e:
        print(f"Invalid number format for issues_number: {e}")
        raise RuntimeError(f"Invalid number format for issues_number: {e}")
    except Exception as e:
        print(f"Failed to list issues: {e}")
        raise RuntimeError(f"Failed to list issues: {e}")


if __name__ == "__main__":
    main() 