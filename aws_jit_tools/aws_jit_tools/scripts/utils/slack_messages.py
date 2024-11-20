from typing import Dict, Any
import json

def create_access_granted_blocks(account_id: str, permission_set: str, duration_seconds: int, user_email: str) -> Dict[str, Any]:
    """Create engaging Slack Block Kit message for access grant notification."""
    
    duration_hours = duration_seconds / 3600
    
    return {
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "🎉 AWS Access Granted! 🎉",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"You've been granted access to AWS account *{account_id}* with permission set *{permission_set}*"
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Duration:*\n{duration_hours} hours"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*User:*\n{user_email}"
                    }
                ]
            },
            {
                "type": "divider"
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*How to Access AWS:*"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*🌐 Web Console*\n• Visit: <https://signin.aws.amazon.com/switchrole?account={account_id}|AWS Console>\n• Choose your SSO login"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*💻 AWS CLI*\n```aws sso login --profile your-profile```\n```aws s3 ls --profile your-profile```"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*🔧 SDK Configuration*\n```python\nimport boto3\nsession = boto3.Session(profile_name='your-profile')\n```"
                }
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": "⏰ Access will expire in {duration_hours} hours"
                    }
                ]
            },
            {
                "type": "divider"
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "Need help? Contact the security team for assistance."
                },
                "accessory": {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "View AWS Docs",
                        "emoji": True
                    },
                    "url": "https://docs.aws.amazon.com/cli/latest/userguide/sso-configure-profile-token.html"
                }
            }
        ]
    }

def create_access_expired_blocks(account_id: str, permission_set: str) -> Dict[str, Any]:
    """Create Slack Block Kit message for access expiration notification."""
    
    return {
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "⚠️ AWS Access Expired",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"Your access to AWS account *{account_id}* with permission set *{permission_set}* has expired."
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "Need to extend your access? Use the Kubiya JIT access tool to request new credentials."
                }
            }
        ]
    }

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