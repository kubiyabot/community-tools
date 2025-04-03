from basic_funcs import (
    get_jira_server_url,
    get_jira_basic_headers,
    setup_client_cert_files,
    get_jira_auth,
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

    server_url = get_jira_server_url()
    comment_url = f"{server_url}/rest/api/2/issue/{args.issue_key}/comment"
    cert_path, key_path = setup_client_cert_files()
    auth = get_jira_auth()
    
    try:
        response = requests.post(
            comment_url, 
            headers=get_jira_basic_headers(), 
            auth=auth,
            data=json.dumps(payload),
            cert=(cert_path, key_path),
            verify=False
        )
        response.raise_for_status()
        print(f"Comment added to issue {args.issue_key} successfully.")
    except Exception as e:
        print(f"Failed to add comment to issue: {e}")
        raise RuntimeError(f"Failed to add comment to issue: {e}")


if __name__ == "__main__":
    main() 