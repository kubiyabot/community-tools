from typing import Dict, Any, Optional
import json

def create_access_granted_blocks(account_id: str, permission_set: str, duration_seconds: int, 
                               user_email: str, account_alias: Optional[str] = None,
                               permission_set_details: Optional[dict] = None) -> Dict[str, Any]:
    """Create engaging Slack Block Kit message for access grant notification."""
    
    duration_hours = duration_seconds / 3600
    account_name = account_alias or account_id
    
    blocks = [
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
                "text": f"You've been granted access to AWS account *{account_name}* ({account_id}) with permission set *{permission_set}*"
            }
        },
        {
            "type": "section",
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": f"*Duration:*\n{duration_hours:.1f} hours"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*User:*\n{user_email}"
                }
            ]
        }
    ]

    # Add permission set details if available
    if permission_set_details:
        description = permission_set_details.get('Description', 'No description available')
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Permission Set Details:*\n{description}"
            }
        })

    # Add access instructions with more detailed steps
    blocks.extend([
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
                "text": f"*🌐 Web Console Access*\n1. Visit: <https://signin.aws.amazon.com/switchrole?account={account_id}|AWS Console>\n2. Sign in with your SSO credentials\n3. Select account *{account_name}* ({account_id})\n4. You should now have access with the *{permission_set}* permission set"
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*💻 AWS CLI Access*\n1. Configure AWS CLI SSO:\n```aws configure sso\nSSO start URL: https://YOUR_SSO_URL\nSSO Region: YOUR_SSO_REGION\nAccount ID: " + account_id + "\nRole name: " + permission_set + "\nCLI profile name: [choose-a-name]```\n2. Login and get credentials:\n```aws sso login```\n3. Test your access:\n```aws sts get-caller-identity```"
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*🔧 AWS SDK Configuration (Python)*\n```python\nimport boto3\nsession = boto3.Session()\ns3 = session.client('s3')\n# The session will use your SSO credentials automatically```"
            }
        },
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f"⏰ Access will expire in {duration_hours:.1f} hours"
                }
            ]
        }
    ])

    # Return blocks wrapped in a dictionary
    return {"blocks": blocks}

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

def create_s3_access_granted_blocks(account_id: str, user_email: str, 
                                    policy_template: str, duration_seconds: int,
                                    bucket_name: str) -> Dict[str, Any]:
    """Create Slack message blocks for S3 access granted notification."""

    duration_hours = duration_seconds / 3600

    return {
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "🎉 S3 Access Granted! 🎉",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"You've been granted *{policy_template}* access to S3 bucket *{bucket_name}*."
                }
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Duration:*\n{duration_hours:.1f} hours"},
                    {"type": "mrkdwn", "text": f"*User:*\n{user_email}"}
                ]
            },
            {
                "type": "divider"
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*How to Access the S3 Bucket:*\nYou can use your AWS credentials to access the bucket via AWS CLI, SDKs, or the AWS Console."
                }
            },
            {
                "type": "context",
                "elements": [
                    {"type": "mrkdwn", "text": "⚠️ Remember to adhere to data security policies while accessing S3 resources."}
                ]
            }
        ]
    }

def create_s3_access_revoked_blocks(user_email: str, bucket_name: str) -> Dict[str, Any]:
    """Create Slack message blocks for S3 access revoked notification."""

    return {
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "🔒 S3 Access Revoked",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"Your access to S3 bucket *{bucket_name}* has been revoked."
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