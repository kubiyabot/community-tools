from typing import List

from basic_funcs import (
    get_jira_cloud_id,
    get_jira_basic_headers,
    ATLASSIAN_JIRA_API_URL,
)

import requests


def list_issues_in_project(
    project_key: str,
    num_issues: int = 5,
    status: str = None,
    assignee: str = None,
    priority: str = None,
    reporter: str = None,
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

    params = {
        "jql": jql_query,
        "maxResults": num_issues,
        "fields": "summary,created",
    }
    try:
        search_url = (
            f"{ATLASSIAN_JIRA_API_URL}/{get_jira_cloud_id()}/rest/api/3/search/jql"
        )
        response = requests.get(
            search_url, headers=get_jira_basic_headers(), params=params
        )
        response.raise_for_status()

        issues = response.json().get("issues", [])
        latest_issues = [
            {
                "key": issue["key"],
                "summary": issue["fields"]["summary"],
                "created": issue["fields"]["created"],
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
    parser.add_argument("project_key", help="Jira Project key")
    parser.add_argument(
        "--issues_number", default=5, type=int, help="Number of issue to list"
    )
    parser.add_argument(
        "--status", default=None, type=str, help="Issues status, such as Done"
    )
    parser.add_argument(
        "--assignee", default=None, type=str, help="including assignee user"
    )
    parser.add_argument(
        "--priority", default=None, type=str, help="including issues priority"
    )
    parser.add_argument(
        "--reporter", default=None, type=str, help="including assignee reporter"
    )
    args = parser.parse_args()

    no_value = "<no value>"  # when no value is injected

    try:
        latest_issues = list_issues_in_project(
            args.project_key,
            args.issues_number if args.issues_number != no_value else 5,
            args.status if args.status != no_value else None,
            args.assignee if args.assignee != no_value else None,
            args.priority if args.priority != no_value else None,
            args.reporter if args.reporter != no_value else None,
        )
        for issue in latest_issues:
            print(
                f"{issue['key']}: {issue['summary']} - Created on {issue['created']})"
            )

    except Exception as e:
        print(f"Failed to list issues: {e}")
        raise RuntimeError(f"Failed to list issues: {e}")


if __name__ == "__main__":
    main()
