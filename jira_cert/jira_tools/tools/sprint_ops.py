import json
import requests
from typing import List, Optional
from basic_funcs import (
    get_jira_server_url,
    get_jira_basic_headers,
    setup_client_cert_files,
    get_jira_auth,
)

def create_sprint(board_id: int, name: str, goal: str = None, start_date: str = None, end_date: str = None) -> dict:
    """Create a new sprint"""
    server_url = get_jira_server_url()
    create_url = f"{server_url}/rest/agile/1.0/sprint"
    cert_path, key_path = setup_client_cert_files()
    auth = get_jira_auth()
    
    payload = {
        "name": name,
        "originBoardId": board_id
    }
    if goal:
        payload["goal"] = goal
    if start_date:
        payload["startDate"] = start_date
    if end_date:
        payload["endDate"] = end_date

    response = requests.post(
        create_url,
        headers=get_jira_basic_headers(),
        auth=auth,
        cert=(cert_path, key_path),
        verify=False,
        data=json.dumps(payload)
    )
    response.raise_for_status()
    return response.json()

def get_sprint_status(sprint_id: int) -> dict:
    """Get sprint details and status"""
    server_url = get_jira_server_url()
    sprint_url = f"{server_url}/rest/agile/1.0/sprint/{sprint_id}"
    cert_path, key_path = setup_client_cert_files()
    
    response = requests.get(
        sprint_url,
        headers=get_jira_basic_headers(),
        cert=(cert_path, key_path),
        verify=False
    )
    response.raise_for_status()
    return response.json()

def update_sprint_state(sprint_id: int, state: str) -> dict:
    """Update sprint state (start/close)"""
    server_url = get_jira_server_url()
    state_url = f"{server_url}/rest/agile/1.0/sprint/{sprint_id}"
    cert_path, key_path = setup_client_cert_files()
    
    if state not in ["active", "closed"]:
        raise ValueError("State must be either 'active' or 'closed'")
    
    payload = {"state": state}
    response = requests.post(
        state_url,
        headers=get_jira_basic_headers(),
        cert=(cert_path, key_path),
        verify=False,
        data=json.dumps(payload)
    )
    response.raise_for_status()
    return response.json()

def move_issues_to_sprint(sprint_id: int, issue_keys: List[str]) -> bool:
    """Move issues to a sprint"""
    server_url = get_jira_server_url()
    move_url = f"{server_url}/rest/agile/1.0/sprint/{sprint_id}/issue"
    cert_path, key_path = setup_client_cert_files()
    
    payload = {
        "issues": issue_keys
    }
    response = requests.post(
        move_url,
        headers=get_jira_basic_headers(),
        cert=(cert_path, key_path),
        verify=False,
        data=json.dumps(payload)
    )
    response.raise_for_status()
    return True

def get_sprint_issues(sprint_id: int) -> List[dict]:
    """Get all issues in a sprint"""
    server_url = get_jira_server_url()
    issues_url = f"{server_url}/rest/agile/1.0/sprint/{sprint_id}/issue"
    cert_path, key_path = setup_client_cert_files()
    
    response = requests.get(
        issues_url,
        headers=get_jira_basic_headers(),
        cert=(cert_path, key_path),
        verify=False
    )
    response.raise_for_status()
    return response.json()["issues"]

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Manage Jira sprints")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Create sprint parser
    create_parser = subparsers.add_parser("create", help="Create a new sprint")
    create_parser.add_argument("board_id", type=int, help="Board ID")
    create_parser.add_argument("name", help="Sprint name")
    create_parser.add_argument("--goal", help="Sprint goal")
    create_parser.add_argument("--start-date", help="Sprint start date (YYYY-MM-DD)")
    create_parser.add_argument("--end-date", help="Sprint end date (YYYY-MM-DD)")
    
    # Get sprint status parser
    status_parser = subparsers.add_parser("status", help="Get sprint status")
    status_parser.add_argument("sprint_id", type=int, help="Sprint ID")
    
    # Update sprint state parser
    state_parser = subparsers.add_parser("state", help="Update sprint state")
    state_parser.add_argument("sprint_id", type=int, help="Sprint ID")
    state_parser.add_argument("state", choices=["active", "closed"], help="New sprint state")
    
    # Move issues parser
    move_parser = subparsers.add_parser("move", help="Move issues to sprint")
    move_parser.add_argument("sprint_id", type=int, help="Sprint ID")
    move_parser.add_argument("issue_keys", nargs="+", help="Issue keys to move")
    
    # List sprint issues parser
    list_parser = subparsers.add_parser("list", help="List sprint issues")
    list_parser.add_argument("sprint_id", type=int, help="Sprint ID")
    
    args = parser.parse_args()
    
    try:
        if args.command == "create":
            result = create_sprint(args.board_id, args.name, args.goal, args.start_date, args.end_date)
            print(f"✅ Sprint created successfully: {json.dumps(result, indent=2)}")
        
        elif args.command == "status":
            result = get_sprint_status(args.sprint_id)
            print(f"Sprint status: {json.dumps(result, indent=2)}")
        
        elif args.command == "state":
            result = update_sprint_state(args.sprint_id, args.state)
            print(f"✅ Sprint state updated to {args.state}: {json.dumps(result, indent=2)}")
        
        elif args.command == "move":
            move_issues_to_sprint(args.sprint_id, args.issue_keys)
            print(f"✅ Successfully moved issues to sprint {args.sprint_id}")
        
        elif args.command == "list":
            issues = get_sprint_issues(args.sprint_id)
            print(f"Sprint issues: {json.dumps(issues, indent=2)}")
        
    except Exception as e:
        print(f"❌ Operation failed: {str(e)}")
        raise RuntimeError(f"Sprint operation failed: {str(e)}")

if __name__ == "__main__":
    main() 