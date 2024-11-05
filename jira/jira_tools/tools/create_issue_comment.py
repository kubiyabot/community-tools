from basic_funcs import (
    get_jira_cloud_id,
    get_jira_basic_headers,
    ATLASSIAN_JIRA_API_URL,
)

import json
import requests


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Create Jira issue")
    parser.add_argument("issue_key", help="The key of the Jira issue")
    parser.add_argument("comment", help="The comment text to add.")

    args = parser.parse_args()

    payload = {
        "body": {
            "content": [
                {
                    "content": [{"text": args.comment, "type": "text"}],
                    "type": "paragraph",
                }
            ],
            "type": "doc",
            "version": 1,
        }
    }

    comment_url = f"{ATLASSIAN_JIRA_API_URL}/{get_jira_cloud_id()}/rest/api/3/issue/{args.issue_key}/comment"
    try:
        response = requests.post(
            comment_url, headers=get_jira_basic_headers(), data=json.dumps(payload)
        )
        response.raise_for_status()
        print(f"Comment added to issue {args.issue_key} successfully.")
    except Exception as e:
        print(f"Failed to added to comment issue: {e}")
        raise RuntimeError(f"Failed to added to comment issue: {e}")


if __name__ == "__main__":
    main()
