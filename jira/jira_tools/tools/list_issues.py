from typing import List
from kubiya_sdk.tools import Tool, Arg
from basic_funcs import (
    get_jira_cloud_id,
    get_jira_basic_headers,
    ATLASSIAN_JIRA_API_URL,
)
from ..base import JiraPythonTool, register_jira_tool
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


class ListIssuesInProject(JiraPythonTool):
    def __init__(self):
        super().__init__(
            name="list_issues",
            description="List Jira issues in a project",
            content=self.run,
            args=[
                Arg("project_key", str, "Jira Project key"),
                Arg("issues_number", int, "Number of issues to list", default=5),
                Arg("status", str, "Issues status, such as Done", default=None),
                Arg("assignee", str, "Filter by assignee", default=None),
                Arg("priority", str, "Filter by priority", default=None),
                Arg("reporter", str, "Filter by reporter", default=None),
            ],
        )

    def run(self, args):
        try:
            latest_issues = list_issues_in_project(
                args.project_key,
                args.issues_number,
                args.status,
                args.assignee,
                args.priority,
                args.reporter,
            )
            for issue in latest_issues:
                print(
                    f"{issue['key']}: {issue['summary']} - Created on {issue['created']})"
                )
            return latest_issues

        except Exception as e:
            print(f"Failed to list issues: {e}")
            raise RuntimeError(f"Failed to list issues: {e}")

# Register the tool
register_jira_tool(ListIssuesInProject())

if __name__ == "__main__":
    import sys
    tool = ListIssuesInProject()
    tool.run(tool.parse_args(sys.argv[1:]))
