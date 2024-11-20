def create_access_revoked_blocks(account_id: str, permission_set: str, user_email: str) -> Dict[str, Any]:
    """Create Slack Block Kit message for access revocation notification."""
    
    return {
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "🔒 AWS Access Revoked",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"Your access to AWS account *{account_id}* with permission set *{permission_set}* has been revoked."
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "If you believe this is a mistake, please contact the security team."
                }
            }
        ]
    } 