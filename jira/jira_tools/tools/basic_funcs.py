import os

import requests
from requests.exceptions import HTTPError

ATLASSIAN_RESOURCES_URL = "https://api.atlassian.com/oauth/token/accessible-resources"
ATLASSIAN_JIRA_API_URL = "https://api.atlassian.com/ex/jira"


def _get_jira_token() -> str:
    token = os.getenv("JIRA_OAUTH_TOKEN", "")

    if not token:
        raise ValueError(
            "JIRA_OAUTH_TOKEN environment variable is not set. "
            "You need to set up jira integration for your teammate agent...")

    return token


def get_jira_cloud_id() -> str:
    headers = {
        "Authorization": f"Bearer {_get_jira_token()}",
        "Accept": "application/json",
    }
    try:
        response = requests.get(ATLASSIAN_RESOURCES_URL, headers=headers)
        response.raise_for_status()
        resources = response.json()
        workspaces = [resources["name"] for resources in resources]
        if len(resources) > 1:
            print(f"WARNING: You have more than one workspace, available workspaces: {workspaces}. "
                  f"The first one will be used...")
        return resources[0]["id"]

    except HTTPError as e:
        print(f"Failed from Jira api server: {e}")
        raise RuntimeError(f"Failed from Jira api server: {e}")


def get_jira_user_id(email: str) -> str:
    jira_cloud_id = get_jira_cloud_id()
    user_search_url = (
        f"{ATLASSIAN_JIRA_API_URL}/{jira_cloud_id}/rest/api/3/user/search?query={email}"
    )

    headers = {
        "Authorization": f"Bearer {_get_jira_token()}",
        "Accept": "application/json",
    }
    try:
        response = requests.get(user_search_url, headers=headers)
        response.raise_for_status()
        return response.json()[0]["accountId"]
    except HTTPError as e:
        print(f"Failed from Jira api server: {e}")
        raise RuntimeError(f"Failed from Jira api server: {e}")


def get_jira_basic_headers() -> dict:
    return {
        "Authorization": f"Bearer {_get_jira_token()}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
