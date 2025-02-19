from basic_funcs import (
    get_jira_cloud_id,
    get_jira_basic_headers,
    ATLASSIAN_JIRA_API_URL,
)

import json
import requests


def get_available_transitions(issue_key: str) -> list:
    """Get available transitions for an issue"""
    transitions_url = f"{ATLASSIAN_JIRA_API_URL}/{get_jira_cloud_id()}/rest/api/3/issue/{issue_key}/transitions"
    
    try:
        response = requests.get(transitions_url, headers=get_jira_basic_headers())
        response.raise_for_status()
        return response.json()["transitions"]
    except Exception as e:
        print(f"Failed to get available transitions: {e}")
        raise RuntimeError(f"Failed to get available transitions: {e}")


def transition_issue(issue_key: str, transition_name: str):
    """Transition an issue to a new status"""
    transitions = get_available_transitions(issue_key)
    
    # Find the transition ID that matches the requested name
    transition_id = None
    for transition in transitions:
        if transition["name"].lower() == transition_name.lower():
            transition_id = transition["id"]
            break
    
    if not transition_id:
        available_transitions = ", ".join([t["name"] for t in transitions])
        raise ValueError(
            f"Transition '{transition_name}' not found. Available transitions: {available_transitions}"
        )

    transition_url = f"{ATLASSIAN_JIRA_API_URL}/{get_jira_cloud_id()}/rest/api/3/issue/{issue_key}/transitions"
    
    payload = {
        "transition": {
            "id": transition_id
        }
    }

    try:
        response = requests.post(
            transition_url,
            headers=get_jira_basic_headers(),
            data=json.dumps(payload)
        )
        response.raise_for_status()
        print(f"Successfully transitioned issue {issue_key} to '{transition_name}'")
    except Exception as e:
        print(f"Failed to transition issue: {e}")
        raise RuntimeError(f"Failed to transition issue: {e}")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Transition a Jira issue")
    parser.add_argument("issue_key", help="The key of the Jira issue")
    parser.add_argument("transition", help="The name of the transition (e.g., 'Done')")
    
    args = parser.parse_args()
    
    transition_issue(args.issue_key, args.transition)


if __name__ == "__main__":
    main() 