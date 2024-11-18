from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

class ParsedRequest(BaseModel):
    resource_details: Dict[str, Any]
    vendor: str # AWS, GCP, Azure, GitHub...
    natural_language_description: str
    missing_details_message: str = None

class TerraformCode(BaseModel):
    tf_files: Dict[str, str]
    tf_code_explanation: str

class ApprovalRequest(BaseModel):
    request_id: str
    user_email: str
    purpose: str
    cost: float
    requested_at: datetime
    ttl: str
    expiry_time: datetime
    slack_channel_id: str
    slack_thread_ts: str
    approved: str = 'pending'
    tf_state: str = None

class ResourceEstimation(BaseModel):
    resource_name: str
    resource_type: str
    estimated_cost: float

class ResourceAction(BaseModel):
    request_id: str
    action: str
    timestamp: datetime

class FollowUpAction(BaseModel):
    request_id: str
    action: str
    schedule_time: datetime

class SlackMessage(BaseModel):
    channel: str
    text: str
    blocks: list = None
    thread_ts: str = None

class AWSResource(BaseModel):
    resource_id: str
    resource_type: str
    attributes: dict
