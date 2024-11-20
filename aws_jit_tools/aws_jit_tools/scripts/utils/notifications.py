import logging
from typing import Optional
from .slack_client import SlackClient
from .slack_messages import create_access_granted_blocks, create_access_expired_blocks

logger = logging.getLogger(__name__)

class NotificationManager:
    def __init__(self):
        self.slack = SlackClient()

    def send_access_granted(self, account_id: str, permission_set: str, 
                          duration_seconds: int, user_email: str,
                          account_alias: Optional[str] = None,
                          permission_set_details: Optional[dict] = None) -> bool:
        """Send access granted notification."""
        try:
            blocks = create_access_granted_blocks(
                account_id=account_id,
                permission_set=permission_set,
                duration_seconds=duration_seconds,
                user_email=user_email,
                account_alias=account_alias,
                permission_set_details=permission_set_details
            )
            return self.slack.send_message(
                message="AWS access granted! 🎉",
                blocks=blocks
            )
        except Exception as e:
            logger.error(f"Failed to send access granted notification: {e}")
            return False

    def send_access_expired(self, account_id: str, permission_set: str) -> bool:
        """Send access expired notification."""
        try:
            blocks = create_access_expired_blocks(
                account_id=account_id,
                permission_set=permission_set
            )
            return self.slack.send_message(
                message="AWS access expired",
                blocks=blocks
            )
        except Exception as e:
            logger.error(f"Failed to send access expired notification: {e}")
            return False 