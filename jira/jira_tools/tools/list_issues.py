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
    label: str = None,
)-> List[dict]:

    # Start with the project filter
    jql_query = f"project = {project_key}"
    
    # Add filters, but handle status more flexibly
    if status and status.strip():
        # Use the ~ operator for partial/case-insensitive matching
        jql_query += f" AND status ~ \"{status.strip()}\""
    if assignee and assignee.strip():
        jql_query += f" AND assignee = '{assignee.strip()}'"
    if priority and priority.strip():
        jql_query += f" AND priority = '{priority.strip()}'"
    if reporter and reporter.strip():
        jql_query += f" AND reporter = '{reporter.strip()}'"
    if label and label.strip():
        jql_query += f" AND labels = '{label.strip()}'"
    
    # Add explicit sorting to ensure consistent results
    jql_query += " ORDER BY created ASC"

    print(f"Final JQL Query: {jql_query}")
    
    # Set a reasonable page size for pagination
    page_size = 100
    
    params = {
        "jql": jql_query,
        "maxResults": page_size,
        "fields": "summary,created,labels,assignee,status",
        "startAt": 0
    }
    try:
        search_url = (
            f"{ATLASSIAN_JIRA_API_URL}/{get_jira_cloud_id()}/rest/api/3/search"
        )
        print(f"URL: {search_url}")
        
        response = requests.get(
            search_url, headers=get_jira_basic_headers(), params=params
        )
        response.raise_for_status()
        
        response_json = response.json()
        
        total = response_json.get("total", 0)
        issues = response_json.get("issues", [])
        
        print(f"Total issues matching criteria: {total}")
        print(f"Issues returned in first page: {len(issues)}")
        
        # If there are more issues than returned in the first request, fetch additional pages
        if total > len(issues):
            print(f"Fetching additional pages to get all {total} issues...")
            all_issues = issues.copy()
            
            # Start from the next page
            for start_at in range(page_size, total, page_size):
                print(f"Fetching page starting at {start_at}...")
                params["startAt"] = start_at
                response = requests.get(
                    search_url, headers=get_jira_basic_headers(), params=params
                )
                response.raise_for_status()
                batch = response.json().get("issues", [])
                all_issues.extend(batch)
                print(f"Fetched {len(batch)} more issues, total so far: {len(all_issues)}")
                if len(batch) == 0:
                    break
                
                # If we've reached the requested number of issues, stop fetching more
                if num_issues and len(all_issues) >= num_issues:
                    print(f"Reached requested limit of {num_issues} issues")
                    break
            
            issues = all_issues
            print(f"Total issues fetched: {len(issues)}")
        
        # Limit the results to the requested number if specified
        if num_issues and len(issues) > num_issues:
            print(f"Limiting results to requested {num_issues} issues")
            issues = issues[:num_issues]
        
        # Print details about each issue for debugging (limit to first 20 for readability)
        display_count = min(20, len(issues))
        print(f"Displaying first {display_count} issues:")
        for i, issue in enumerate(issues[:display_count]):
            print(f"Issue {i+1}:")
            print(f"  Key: {issue['key']}")
            print(f"  Summary: {issue['fields']['summary']}")
            assignee_info = issue['fields'].get('assignee')
            assignee_name = assignee_info.get('displayName') if assignee_info else "Unassigned"
            print(f"  Assignee: {assignee_name}")
            status_info = issue['fields'].get('status')
            status_name = status_info.get('name') if status_info else "Unknown"
            print(f"  Status: {status_name}")
        
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