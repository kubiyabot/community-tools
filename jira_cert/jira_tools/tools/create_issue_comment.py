from basic_funcs import (
    get_jira_server_url,
    get_jira_basic_headers,
    setup_client_cert_files,
    get_jira_auth,
    test_jira_connection,
)

import json
import requests
import urllib3

# Suppress only the specific InsecureRequestWarning
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def create_issue_comment(issue_key, comment_text):
    # Test connection first
    if not test_jira_connection():
        print("Failed to establish connection to Jira. Please check your configuration.")
        return False

    # Simpler payload format for Jira Server/Data Center
    payload = {
        "body": comment_text
    }

    server_url = get_jira_server_url()
    comment_url = f"{server_url}/rest/api/2/issue/{issue_key}/comment"
    cert_path, key_path = setup_client_cert_files()
    auth = get_jira_auth()
    headers = get_jira_basic_headers()
    
    # Add browser-like headers similar to list_issues.py
    headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'application/json',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
    })
    
    try:
        response = requests.post(
            comment_url, 
            headers=headers, 
            auth=auth,
            data=json.dumps(payload),
            cert=(cert_path, key_path),
            verify=False
        )
        
        if response.status_code == 403:
            if 'X-Authentication-Denied-Reason' in response.headers:
                if 'CAPTCHA_CHALLENGE' in response.headers['X-Authentication-Denied-Reason']:
                    print("CAPTCHA verification required. Please log in through the web interface first.")
                    print("URL:", response.headers.get('X-Authentication-Denied-Reason').split('login-url=')[1])
                    return False
            
        if response.status_code == 401:
            print("Authentication failed. Please check your credentials and certificates.")
            return False
            
        response.raise_for_status()
        return True
    except requests.exceptions.SSLError as e:
        print("\nSSL Error occurred. Please check your certificates.")
        return False
    except requests.exceptions.RequestException as e:
        print(f"\nError occurred while adding comment: {str(e)}")
        return False


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Create Jira issue comment")
    parser.add_argument("issue_key", help="The key of the Jira issue")
    parser.add_argument("comment", help="The comment text to add.")

    args = parser.parse_args()

    success = create_issue_comment(args.issue_key, args.comment)
    
    if success:
        print(f"Comment added to issue {args.issue_key} successfully.")
    else:
        raise RuntimeError(f"Failed to add comment to issue {args.issue_key}")


if __name__ == "__main__":
    main() 