import warnings
import logging
import urllib3
from typing import List
import json

from basic_funcs import (
    get_jira_server_url,
    get_jira_basic_headers,
    setup_client_cert_files,
    test_jira_connection,
    get_jira_auth,
)

import requests

# Configure logging
logger = logging.getLogger(__name__)

# Suppress only the specific InsecureRequestWarning
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def list_issues_in_project(
    project_key: str,
    num_issues: int = 5,
    status: str = None,
    assignee: str = None,
    priority: str = None,
    reporter: str = None,
    label: str = None,
)-> List[dict]:

    logger.info(f"=== Listing Issues for Project: {project_key} ===")
    
    # Test connection first
    if not test_jira_connection():
        logger.error("Failed to establish connection to Jira. Please check your configuration.")
        return []

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

    logger.info(f"Using JQL query: {jql_query}")

    params = {
        "jql": jql_query,
        "maxResults": num_issues,
        "fields": "summary,created,labels,status",
    }
    logger.info(f"Request parameters: {params}")
    
    try:
        server_url = get_jira_server_url()
        search_url = f"{server_url}/rest/api/2/search"
        logger.info(f"Making request to: {search_url}")
        
        cert_path, key_path = setup_client_cert_files()
        auth = get_jira_auth()
        headers = get_jira_basic_headers()
        logger.info(f"Using headers: {headers}")
        
        logger.info("Sending request...")
        response = requests.get(
            search_url, 
            headers=headers, 
            auth=auth,
            params=params,
            cert=(cert_path, key_path),
            verify=False
        )
        
        logger.info(f"Response status code: {response.status_code}")
        logger.info(f"Response headers: {dict(response.headers)}")
        
        if response.status_code == 401:
            logger.error("Authentication failed. Please check your credentials and certificates.")
            logger.error(f"Response body: {response.text}")
            try:
                error_details = response.json()
                logger.error(f"Error details: {json.dumps(error_details, indent=2)}")
            except:
                logger.error("Could not parse error response as JSON")
            return []
            
        response.raise_for_status()

        data = response.json()
        logger.info(f"Total issues found: {data.get('total', 0)}")
        
        issues = data.get("issues", [])
        latest_issues = [
            {
                "key": issue["key"],
                "summary": issue["fields"]["summary"],
                "created": issue["fields"]["created"],
                "labels": issue["fields"].get("labels", []),
                "status": issue["fields"]["status"]["name"] if "status" in issue["fields"] else "Unknown"
            }
            for issue in issues
        ]

        return latest_issues

    except requests.exceptions.SSLError as e:
        logger.error("\nSSL Error occurred:")
        logger.error(str(e))
        if "certificate verify failed" in str(e):
            logger.error("Certificate verification failed. This might indicate an issue with the certificate format or content.")
        return []
    except requests.exceptions.RequestException as e:
        logger.error("\n=== Request Error ===")
        logger.error(f"Error type: {type(e).__name__}")
        logger.error(f"Error message: {str(e)}")
        if hasattr(e, 'response'):
            logger.error(f"Response status code: {e.response.status_code}")
            logger.error(f"Response headers: {dict(e.response.headers)}")
            logger.error(f"Response body: {e.response.text}")
        if isinstance(e, requests.exceptions.SSLError):
            logger.error("SSL Error - This might indicate a certificate problem")
        elif isinstance(e, requests.exceptions.ConnectionError):
            logger.error("Connection Error - This might indicate a network or URL problem")
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
                f"{issue['key']}: {issue['summary']} - Created on {issue['created']} - Status: {issue['status']}{labels_str}"
            )

    except ValueError as e:
        print(f"Invalid number format for issues_number: {e}")
        raise RuntimeError(f"Invalid number format for issues_number: {e}")
    except Exception as e:
        print(f"Failed to list issues: {e}")
        raise RuntimeError(f"Failed to list issues: {e}")


if __name__ == "__main__":
    main() 