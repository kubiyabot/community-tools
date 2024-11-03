import os

import requests
from requests.exceptions import HTTPError

ATLASSIAN_RESOURCES_URL = "https://api.atlassian.com/oauth/token/accessible-resources"
ATLASSIAN_JIRA_API_URL = "https://api.atlassian.com/ex/jira"


def get_jira_cloud_id() -> str:
    import warnings

    token = os.getenv("JIRA_OAUTH_TOKEN", "")

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
    }
    try:
        response = requests.get(ATLASSIAN_RESOURCES_URL, headers=headers)
        response.raise_for_status()
        resources = response.json()

        if len(resources) > 1:
            warnings.warn("You have more than one workspace, the first one will be used...")
        return resources[0]["id"]

    except HTTPError as e:
        print(f"Failed to get Jira server: {e}")
        return ""


def get_jira_user_id(email: str) -> str:
    jira_cloud_id = get_jira_cloud_id()
    user_search_url = f"{ATLASSIAN_JIRA_API_URL}/{jira_cloud_id}/rest/api/3/user/search?query={email}"

    token = os.getenv("JIRA_OAUTH_TOKEN", "")

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
    }
    try:
        response = requests.get(user_search_url, headers=headers)
        response.raise_for_status()
        return response.json()
    except HTTPError as e:
        print(f"Failed to get Jira server: {e}")
        return ""


def get_jira_basic_headers() -> dict:
    token = os.getenv("JIRA_OAUTH_TOKEN", "")
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

def get_file_content(path) -> bytes:
    with open(path, "rb") as f:
        return f.read()


