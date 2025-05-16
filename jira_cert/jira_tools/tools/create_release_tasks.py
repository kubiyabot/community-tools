import sys
from datetime import datetime

from create_issue import create_issue, test_jira_connection

def validate_date_format(date_str: str) -> bool:
    """Validate if the date string is in the format DD.MM.Y"""
    try:
        datetime.strptime(date_str, "%d.%m.%y")
        return True
    except ValueError:
        return False

def create_release_tasks(release_date: str) -> bool:
    """Create a main release task and subtasks for different environments"""
    # Validate date format
    if not validate_date_format(release_date):
        print(f"❌ Invalid date format: {release_date}. Please use DD.MM.YY format (e.g., 25.05.24)")
        return False
    
    # Test connection first
    if not test_jira_connection():
        print("Failed to establish connection to Jira. Please check your configuration.")
        return False
    
    # Project key for KUBIKA2 board
    project_key = "KUBIKA2"
    
    # Create main task
    main_task_summary = f"Release {release_date}"
    main_task_description = f"Main release task for {release_date}"
    main_task_type = "Task"
    
    # Create the main task
    print(f"Creating main release task: {main_task_summary}")
    main_task_success = create_issue(
        project_key=project_key,
        summary=main_task_summary,
        description=main_task_description,
        issue_type=main_task_type,
        label=f"{release_date},operations,release,new",
        # Priority is set to Major by default in the payload
    )
    
    if not main_task_success:
        print("❌ Failed to create main release task")
        return False
    
    # Get the main task ID from the response
    # Note: We need to modify create_issue to return the issue key
    # For now, we'll assume it's available
    main_task_id = input("Please enter the main task ID that was just created: ")
    
    # Define subtasks
    environments = [
        "[Test] Roll out release",
        "[Prelive] Roll out release",
        "[Prod] Roll out release",
        "[DPRND1] Roll out release",
        "[TEST1] Roll out release",
        "[Prelive1] Roll out release",
        "[MGMT1] Roll out release"
    ]
    
    # Create subtasks
    subtask_success = True
    for env in environments:
        subtask_summary = f"{env} {release_date}"
        subtask_description = f"Roll out release {release_date} to {env.strip('[]')} environment"
        
        print(f"Creating subtask: {subtask_summary}")
        success = create_issue(
            project_key=project_key,
            summary=subtask_summary,
            description=subtask_description,
            issue_type="Sub-task",
            parent_id=main_task_id,
            label=f"{release_date},operations,release"
        )
        
        if not success:
            print(f"❌ Failed to create subtask: {subtask_summary}")
            subtask_success = False
    
    return subtask_success

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Create Jira release tasks")
    parser.add_argument("release_date", help="Release date in DD.MM.YY format (e.g., 25.05.24)")
    args = parser.parse_args()
    
    success = create_release_tasks(args.release_date)
    
    if not success:
        print("❌ Failed to create all release tasks")
        sys.exit(1)
    else:
        print("✅ Successfully created all release tasks")

if __name__ == "__main__":
    main() 