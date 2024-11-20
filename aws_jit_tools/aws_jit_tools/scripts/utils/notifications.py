import logging
from typing import Optional
from .slack_client import SlackClient
from .slack_messages import create_access_granted_blocks, create_access_expired_blocks, create_access_revoked_blocks, create_s3_access_granted_blocks, create_s3_access_revoked_blocks

logger = logging.getLogger(__name__)

class NotificationManager:
    def __init__(self):
        self.slack = SlackClient()

    def send_access_granted(self, account_id: str, permission_set: str, 
                          duration_seconds: int, user_email: str,
                          account_alias: Optional[str] = None,
                          permission_set_details: Optional[dict] = None) -> bool:
        """Send access granted notification to both thread and main channel."""
        try:
            # Create blocks for the message
            blocks = create_access_granted_blocks(
                account_id=account_id,
                permission_set=permission_set,
                duration_seconds=duration_seconds,
                user_email=user_email,
                account_alias=account_alias,
                permission_set_details=permission_set_details
            )

            # Store original thread_ts
            original_thread = self.slack.thread_ts

            try:
                # First send to the thread if thread_ts exists
                if original_thread:
                    self.slack.thread_ts = original_thread
                    self.slack.send_message(
                        message="AWS access granted! 🎉",
                        blocks=blocks  # No need to wrap, already in correct format
                    )

                # Then send to main channel (without thread)
                self.slack.thread_ts = None
                success = self.slack.send_message(
                    message="AWS access granted! 🎉",
                    blocks=blocks  # No need to wrap, already in correct format
                )

                return success

            finally:
                # Restore original thread_ts
                self.slack.thread_ts = original_thread

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

    def send_access_revoked(self, account_id: str, permission_set: str, user_email: str) -> bool:
        """Send access revoked notification directly to the user."""
        try:
            # Look up Slack user ID by email
            slack_user_id = self.slack.lookup_user_by_email(user_email)
            if not slack_user_id:
                logger.error(f"Could not find Slack user ID for email: {user_email}")
                return False

            # Create message blocks
            blocks = create_access_revoked_blocks(
                account_id=account_id,
                permission_set=permission_set,
                user_email=user_email
            )

            # Store original channel and thread
            original_channel = self.slack.channel_id
            original_thread = self.slack.thread_ts

            try:
                # Set channel to user's ID for direct message
                self.slack.channel_id = slack_user_id
                # Clear thread_ts to send to main thread
                self.slack.thread_ts = None

                # Send the message
                success = self.slack.send_message(
                    message="Your AWS access has been revoked.",
                    blocks=blocks
                )

                return success

            finally:
                # Restore original channel and thread
                self.slack.channel_id = original_channel
                self.slack.thread_ts = original_thread

        except Exception as e:
            logger.error(f"Failed to send access revoked notification: {e}")
            return False

    def send_s3_access_granted(self, account_id: str, user_email: str, 
                               policy_template: str, duration_seconds: int,
                               bucket_name: str) -> bool:
        """Send S3 access granted notification."""
        try:
            blocks = create_s3_access_granted_blocks(
                account_id=account_id,
                user_email=user_email,
                policy_template=policy_template,
                duration_seconds=duration_seconds,
                bucket_name=bucket_name
            )
            success = self.slack.send_message(
                message=f"S3 access granted to bucket {bucket_name} for {user_email}",
                blocks=blocks
            )
            return success
        except Exception as e:
            logger.error(f"Failed to send S3 access granted notification: {e}")
            return False

    def send_s3_access_revoked(self, user_email: str, bucket_name: str) -> bool:
        """Send S3 access revoked notification directly to the user."""
        try:
            # Look up Slack user ID by email
            slack_user_id = self.slack.lookup_user_by_email(user_email)
            if not slack_user_id:
                logger.error(f"Could not find Slack user ID for email: {user_email}")
                return False

            # Create message blocks
            blocks = create_s3_access_revoked_blocks(
                user_email=user_email,
                bucket_name=bucket_name
            )

            # Store original channel and thread
            original_channel = self.slack.channel_id
            original_thread = self.slack.thread_ts

            try:
                # Set channel to user's ID for direct message
                self.slack.channel_id = slack_user_id
                # Clear thread_ts to send to main thread
                self.slack.thread_ts = None

                # Send the message
                success = self.slack.send_message(
                    message="Your S3 access has been revoked.",
                    blocks=blocks
                )

                return success

            finally:
                # Restore original channel and thread
                self.slack.channel_id = original_channel
                self.slack.thread_ts = original_thread

        except Exception as e:
            logger.error(f"Failed to send S3 access revoked notification: {e}")
            return False
