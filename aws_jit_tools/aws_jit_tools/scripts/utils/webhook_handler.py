import os
import logging
import requests
import json
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class WebhookHandler:
    def __init__(self):
        self.webhook_url = os.environ.get('REVOKATION_WEBHOOK_URL')
        if not self.webhook_url:
            logger.warning("REVOKATION_WEBHOOK_URL not set")

    def send_revocation_webhook(self, 
                              user_email: str,
                              access_type: str,
                              policy_details: Dict[str, Any],
                              duration_seconds: int,
                              account_id: str,
                              permission_set: Optional[str] = None,
                              buckets: Optional[list] = None) -> bool:
        """Send revocation webhook to Kubiya API."""
        if not self.webhook_url:
            logger.error("REVOKATION_WEBHOOK_URL not configured")
            return False

        try:
            # Determine the revoke tool name based on access type
            if buckets and os.environ.get('POLICY_TEMPLATE'):
                # S3 access case
                revoke_tool_name = f"s3_revoke_{policy_details.get('name', '').lower().replace(' ', '_')}"
            else:
                # SSO access case
                revoke_tool_name = f"jit_session_revoke_{permission_set.lower().replace(' ', '_')}"

            payload = {
                "user_email": user_email,
                "tool_name": revoke_tool_name,
                "tool_params": {
                    "user_email": user_email,
                },
                "access_details": {
                    "type": access_type,
                    "account_id": account_id,
                    "permission_set": permission_set,
                    "buckets": buckets,
                    "policy_details": policy_details,
                    "duration_seconds": duration_seconds
                },
                "status": "pending_revocation"
            }

            response = requests.post(
                self.webhook_url,
                json=payload,
                headers={"Content-Type": "application/json"}
            )

            if response.status_code >= 400:
                logger.error(f"Failed to send revocation webhook: {response.text}")
                return False

            logger.info("Revocation webhook sent successfully")
            return True

        except Exception as e:
            logger.error(f"Error sending revocation webhook: {str(e)}")
            return False 