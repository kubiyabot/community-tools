#!/usr/bin/env python3
import os
import sys
import json
import subprocess
import time
import re
from typing import List, Dict, Any, Optional
from pathlib import Path
from terraform_tools.error_handler import handle_script_error, ScriptError, validate_environment_vars, logger

# Try to import slack_sdk
try:
    from slack_sdk import WebClient
    SLACK_AVAILABLE = True
except ImportError:
    SLACK_AVAILABLE = False
    logger.warning("slack_sdk not available. Slack notifications will be disabled.")

def print_progress(message: str, emoji: str) -> None:
    """Print progress messages with emoji."""
    logger.info(f"{emoji} {message}")

class SlackNotifier:
    def __init__(self):
        """Initialize Slack client with error handling."""
        self.enabled = SLACK_AVAILABLE
        self.start_time = time.time()
        if not self.enabled:
            return

        try:
            validate_environment_vars("SLACK_API_TOKEN", "SLACK_CHANNEL_ID")
            self.client = WebClient(token=os.environ["SLACK_API_TOKEN"])
            self.channel = os.environ["SLACK_CHANNEL_ID"]
            self.message_ts = None
            self.thread_ts = os.environ.get("SLACK_THREAD_TS")
        except ScriptError as e:
            logger.warning(str(e))
            self.enabled = False
        except Exception as e:
            logger.warning(f"Failed to initialize Slack: {str(e)}")
            self.enabled = False

    def send_initial_message(self, text: str) -> None:
        """Send initial message and store timestamp."""
        if not self.enabled:
            return

        try:
            response = self.client.chat_postMessage(
                channel=self.channel,
                text=text,
                thread_ts=self.thread_ts
            )
            self.message_ts = response["ts"]
        except Exception as e:
            logger.error(f"Failed to send Slack message: {str(e)}")
            self.enabled = False

    def update_progress(self, text: str, blocks: Optional[List[Dict[str, Any]]] = None) -> None:
        """Update Slack message with new text and blocks."""
        if not self.enabled or not self.message_ts:
            return

        try:
            self.client.chat_update(
                channel=self.channel,
                ts=self.message_ts,
                text=text,
                blocks=blocks
            )
        except Exception as e:
            logger.error(f"Failed to update Slack message: {str(e)}")
            self.enabled = False

    def send_error(self, error_message: str) -> None:
        """Send error message to Slack."""
        if not self.enabled:
            return

        try:
            self.client.chat_postMessage(
                channel=self.channel,
                text=f":x: Error: {error_message}",
                thread_ts=self.message_ts or self.thread_ts
            )
        except Exception as e:
            logger.error(f"Failed to send error message to Slack: {str(e)}")
            self.enabled = False

def run_command(cmd: List[str], cwd: Optional[Path] = None, capture_output: bool = False) -> Optional[str]:
    """Run a command with enhanced error handling in specified directory."""
    print_progress(f"Running command in {cwd or '.'}: {' '.join(cmd)}", "🔄")
    env = os.environ.copy()
    env["TF_IN_AUTOMATION"] = "1"
    
    try:
        result = subprocess.run(
            cmd,
            cwd=str(cwd) if cwd else None,
            check=True,
            capture_output=capture_output,
            text=True,
            env=env
        )
        if capture_output:
            return result.stdout
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr if e.stderr else str(e)
        logger.error(f"Command failed in {cwd or '.'}: {' '.join(cmd)}\n{error_msg}")
        raise ScriptError(f"Command failed: {' '.join(cmd)}\n{error_msg}", exit_code=e.returncode)
    except Exception as e:
        logger.error(f"Unexpected error running command in {cwd or '.'}: {str(e)}")
        raise ScriptError(f"Unexpected error: {str(e)}", exit_code=1)

def validate_module_path(module_path: Path) -> None:
    """Validate that the module path exists and contains Terraform files."""
    if not module_path.exists():
        raise ScriptError(f"Module path does not exist: {module_path}", exit_code=2)
    
    tf_files = list(module_path.glob("*.tf"))
    if not tf_files:
        raise ScriptError(f"No Terraform files found in module path: {module_path}", exit_code=2)

@handle_script_error
def main():
    # Validate required environment variables
    validate_environment_vars("MODULE_PATH", "WORKSPACE_NAME")
    
    module_path = Path(os.environ["MODULE_PATH"])
    workspace_name = os.environ["WORKSPACE_NAME"]
    
    print_progress(f"Starting Terraform plan for workspace '{workspace_name}'...", "🚀")
    slack = SlackNotifier()
    slack.send_initial_message(f"Starting Terraform plan for workspace '{workspace_name}'...")

    try:
        # Validate module path
        validate_module_path(module_path)
        logger.info(f"Using module path: {module_path}")

        # Validate terraform.tfvars.json exists in module path
        tfvars_path = module_path / 'terraform.tfvars.json'
        if not tfvars_path.exists():
            raise ScriptError(
                f"terraform.tfvars.json not found in module path: {module_path}. "
                "Please run prepare_tfvars.py first.", 
                exit_code=2
            )

        # Initialize Terraform
        print_progress("Initializing Terraform...", "⚙️")
        slack.update_progress("Initializing Terraform...")
        run_command(["terraform", "init"], cwd=module_path)

        # Generate plan
        print_progress("Generating Terraform plan...", "📋")
        slack.update_progress("Generating Terraform plan...")
        plan_output = run_command(
            ["terraform", "plan", "-no-color"],
            cwd=module_path,
            capture_output=True
        )
        print(plan_output)

        # Parse plan output for changes summary
        changes_summary = {
            'add': re.search(r'Plan: (\d+) to add', plan_output or ''),
            'change': re.search(r'(\d+) to change', plan_output or ''),
            'destroy': re.search(r'(\d+) to destroy', plan_output or '')
        }
        
        summary_text = "Plan Summary:\n"
        summary_text += f"🟢 To add: {changes_summary['add'].group(1) if changes_summary['add'] else '0'}\n"
        summary_text += f"🟡 To change: {changes_summary['change'].group(1) if changes_summary['change'] else '0'}\n"
        summary_text += f"🔴 To destroy: {changes_summary['destroy'].group(1) if changes_summary['destroy'] else '0'}"
        
        slack.update_progress(f"Terraform plan completed successfully.\n{summary_text}")

    except ScriptError as e:
        logger.error(f"Error during Terraform plan: {e.message}")
        slack.send_error(e.message)
        raise
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Unexpected error during Terraform plan: {error_msg}")
        slack.send_error(error_msg)
        raise ScriptError(error_msg, exit_code=1)

    print_progress("Terraform plan completed successfully.", "✅")
    print(summary_text)

if __name__ == "__main__":
    main() 