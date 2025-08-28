import os
import sys
import json
import requests
from typing import Optional, Dict, Any, List


def clean_issue_data(issue: Dict[str, Any]) -> Dict[str, Any]:
    """Clean issue data by removing superfluous fields."""
    if not isinstance(issue, dict):
        return issue
    
    # Create a clean copy of the issue
    cleaned_issue = {
        'key': issue.get('key'),
        'id': issue.get('id'),
        'self': issue.get('self')
    }
    
    # Clean fields
    fields = issue.get('fields', {})
    if fields:
        cleaned_fields = {}
        
        # Keep essential fields
        essential_fields = ['summary', 'created', 'updated']
        for field in essential_fields:
            if field in fields:
                cleaned_fields[field] = fields[field]
        
        # Clean issuetype
        if 'issuetype' in fields:
            issuetype = fields['issuetype']
            cleaned_fields['issuetype'] = {
                'id': issuetype.get('id'),
                'name': issuetype.get('name'),
                'description': issuetype.get('description')
            }
        
        # Clean project
        if 'project' in fields:
            project = fields['project']
            cleaned_fields['project'] = {
                'id': project.get('id'),
                'key': project.get('key'),
                'name': project.get('name')
            }
        
        # Clean reporter
        if 'reporter' in fields:
            reporter = fields['reporter']
            cleaned_fields['reporter'] = {
                'accountId': reporter.get('accountId'),
                'displayName': reporter.get('displayName'),
                'active': reporter.get('active')
            }
        
        # Clean assignee
        if 'assignee' in fields:
            assignee = fields['assignee']
            cleaned_fields['assignee'] = {
                'accountId': assignee.get('accountId'),
                'displayName': assignee.get('displayName'),
                'active': assignee.get('active')
            }
        
        # Clean status
        if 'status' in fields:
            status = fields['status']
            cleaned_status = {
                'id': status.get('id'),
                'name': status.get('name'),
                'description': status.get('description')
            }
            
            # Clean status category if it exists
            if 'statusCategory' in status:
                status_category = status['statusCategory']
                cleaned_status['statusCategory'] = {
                    'id': status_category.get('id'),
                    'key': status_category.get('key'),
                    'name': status_category.get('name'),
                    'colorName': status_category.get('colorName')
                }
            
            cleaned_fields['status'] = cleaned_status
        
        cleaned_issue['fields'] = cleaned_fields
    
    return cleaned_issue


def clean_response_data(response_data: Dict[str, Any]) -> Dict[str, Any]:
    """Clean the entire response data by cleaning each issue."""
    cleaned_response = {
        'total': response_data.get('total'),
        'maxResults': response_data.get('maxResults'),
        'startAt': response_data.get('startAt'),
        'isLast': response_data.get('isLast')
    }
    
    # Clean each issue
    issues = response_data.get('issues', [])
    cleaned_issues = [clean_issue_data(issue) for issue in issues]
    cleaned_response['issues'] = cleaned_issues
    
    return cleaned_response


def get_my_tickets(status_filter: Optional[str] = None, max_results: int = 500) -> Dict[str, Any]:
    """Get tickets assigned to the current user from Jira."""
    
    # Get environment variables
    jira_url = os.getenv('JIRA_URL')
    jira_email = os.getenv('JIRA_EMAIL')
    jira_api_key = os.getenv('JIRA_API_KEY')
    kubiya_user_email = os.getenv('KUBIYA_USER_EMAIL')
    
    # Validate required environment variables
    if not all([jira_url, jira_email, jira_api_key]):
        raise ValueError("Missing required environment variables: JIRA_URL, JIRA_EMAIL, JIRA_API_KEY")
    
    if not kubiya_user_email:
        raise ValueError("KUBIYA_USER_EMAIL environment variable is required")
    
    # Clean up URL format
    jira_url = jira_url.rstrip('/')
    if not jira_url.startswith(('http://', 'https://')):
        jira_url = f"https://{jira_url}"
    
    # Build JQL query
    jql = f'assignee = "{kubiya_user_email}"'
    
    if status_filter:
        if status_filter.lower() == 'open':
            jql += ' AND statusCategory != Done'
        elif status_filter.lower() == 'closed':
            jql += ' AND statusCategory = Done'
        else:
            jql += f' AND status = "{status_filter}"'
    else:
        # Default: get non-done tickets
        jql += ' AND statusCategory != Done'
    
    jql += ' ORDER BY created DESC'
    
    # API endpoint
    url = f"{jira_url}/rest/api/3/search"
    
    # Request parameters
    params = {
        'jql': jql,
        'maxResults': min(max_results, 100),  # Jira API limit per request
        'fields': 'key,summary,status,assignee,reporter,created,updated,issuetype,project'
    }
    
    # Headers
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }
    
    # Authentication
    auth = (jira_email, jira_api_key)
    
    all_issues = []
    start_at = 0
    total_results = 0
    
    while True:
        params['startAt'] = start_at
        
        try:
            response = requests.get(url, params=params, headers=headers, auth=auth)
            response.raise_for_status()
            
            data = response.json()
            
            # Set total on first page
            if start_at == 0:
                total_results = data.get('total', 0)
            
            issues = data.get('issues', [])
            all_issues.extend(issues)
            
            # Check if we've reached the limit or end of results
            if len(all_issues) >= max_results or data.get('isLast', True):
                break
            
            # Move to next page
            start_at += 100
            
        except requests.exceptions.RequestException as e:
            print(f"❌ API call failed: {str(e)}", file=sys.stderr)
            if hasattr(e, 'response') and e.response is not None:
                print(f"Response status: {e.response.status_code}", file=sys.stderr)
                try:
                    error_data = e.response.json()
                    if 'errorMessages' in error_data:
                        print("Error details:", file=sys.stderr)
                        for msg in error_data['errorMessages']:
                            print(f"  • {msg}", file=sys.stderr)
                except:
                    print(f"Response text: {e.response.text}", file=sys.stderr)
            raise
    
    # Return the complete response
    result = {
        'total': total_results,
        'maxResults': max_results,
        'startAt': 0,
        'isLast': True,
        'issues': all_issues
    }
    
    return result


def main(status_filter: Optional[str] = None, max_results: int = 500, clean_output: bool = True):
    """Main function to get and return tickets as JSON."""
    try:
        # Get tickets
        result = get_my_tickets(status_filter=status_filter, max_results=max_results)
        
        # Clean the output if requested
        if clean_output:
            result = clean_response_data(result)
        
        # Return the JSON data
        print(json.dumps(result, indent=2))
        
    except Exception as e:
        print(f"❌ Error: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    import argparse
    
    # Command-line argument parsing
    parser = argparse.ArgumentParser(description="Get my Jira tickets")
    parser.add_argument('--status_filter', help='Status filter (open, closed, or specific status)')
    parser.add_argument('--max_results', type=int, default=500, help='Maximum number of results')
    parser.add_argument('--raw', action='store_true', help='Output raw JSON without cleaning')
    
    args = parser.parse_args()
    
    # Call the main function with parsed arguments
    main(
        status_filter=args.status_filter,
        max_results=args.max_results,
        clean_output=not args.raw
    ) 
