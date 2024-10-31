from typing import List, Dict, Any, Optional

def get_header_block(text: str) -> Dict[str, Any]:
    return {
        "type": "header",
        "text": {
            "type": "plain_text",
            "text": text,
            "emoji": True
        }
    }

def get_context_block() -> Dict[str, Any]:
    return {
        "type": "context",
        "elements": [
            {
                "type": "image",
                "image_url": "https://static-00.iconduck.com/assets.00/terraform-icon-452x512-ildgg5fd.png",
                "alt_text": "terraform"
            },
            {
                "type": "mrkdwn",
                "text": "*Phase ${phase} of 4* • Databricks Workspace Deployment"
            }
        ]
    }

def get_workspace_info_block(workspace_name: str, region: str) -> Dict[str, Any]:
    return {
        "type": "section",
        "fields": [
            {
                "type": "mrkdwn",
                "text": f"*Workspace:*\n`{workspace_name}`"
            },
            {
                "type": "mrkdwn",
                "text": f"*Region:*\n`{region}`"
            }
        ]
    }

def get_message_block(message: str) -> Dict[str, Any]:
    return {
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": message
        }
    }

def get_plan_block(plan_output: str) -> Dict[str, Any]:
    return {
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": f"*Terraform Plan:*\n```{plan_output}```"
        }
    }

def get_workspace_button_block(workspace_url: str) -> Dict[str, Any]:
    return {
        "type": "actions",
        "elements": [
            {
                "type": "button",
                "text": {
                    "type": "plain_text",
                    "text": "Open Workspace",
                    "emoji": True
                },
                "url": workspace_url,
                "style": "primary"
            }
        ]
    }

def get_divider_block() -> Dict[str, Any]:
    return {"type": "divider"}

def build_message_blocks(
    status: str,
    message: str,
    phase: str,
    workspace_name: str,
    region: str,
    plan_output: Optional[str] = None,
    workspace_url: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Build a complete message block structure."""
    blocks = [
        get_header_block(status),
        get_context_block(),
        get_workspace_info_block(workspace_name, region),
        get_divider_block(),
        get_message_block(message)
    ]

    if plan_output:
        # Truncate plan if too long
        max_length = 2900
        if len(plan_output) > max_length:
            plan_output = plan_output[:max_length] + "...\n(Output truncated)"
        blocks.append(get_plan_block(plan_output))

    if workspace_url:
        blocks.append(get_workspace_button_block(workspace_url))

    return blocks 