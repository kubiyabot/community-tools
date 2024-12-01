#!/usr/bin/env python3
import os
import sys
import subprocess
import time
from typing import List, Dict, Any, Optional

# Try to import slack_sdk
try:
    from slack_sdk import WebClient
    SLACK_AVAILABLE = True
except ImportError:
    SLACK_AVAILABLE = False
    print("Warning: slack_sdk not available. Slack notifications will be disabled.")

def print_progress(message: str, emoji: str) -> None:
    """Print progress messages with emoji."""
    print(f"{emoji} {message}", flush=True)

class SlackNotifier:
    def __init__(self):
        """Initialize Slack client with error handling."""
        self.enabled = SLACK_AVAILABLE
        self.start_time = time.time()
        if not self.enabled:
            return

        try:
            self.client = WebClient(token=os.environ["SLACK_API_TOKEN"])
            self.channel = os.environ["SLACK_CHANNEL_ID"]
            self.message_ts = None
            self.thread_ts = os.environ.get("SLACK_THREAD_TS")
        except KeyError as e:
            print(f"Warning: Missing Slack environment variable: {e}. Slack notifications will be disabled.")
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
            print(f"Warning: Failed to send Slack message: {str(e)}")
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
            print(f"Warning: Failed to update Slack message: {str(e)}")
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
            print(f"Warning: Failed to send error message to Slack: {str(e)}")
            self.enabled = False

def run_command(cmd: List[str], capture_output: bool = False) -> Optional[str]:
    """Run a command and return its output if capture_output is True."""
    print_progress(f"Running command: {' '.join(cmd)}", "🔄")
    env = os.environ.copy()
    env["TF_IN_AUTOMATION"] = "1"
    try:
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=capture_output,
            text=True,
            env=env
        )
        if capture_output:
            return result.stdout
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr or str(e)
        print(f"❌ Command failed: {' '.join(cmd)}\n{error_msg}", file=sys.stderr)
        raise RuntimeError(f"Command failed: {' '.join(cmd)}\n{error_msg}")

def main():
    print_progress("Starting Terraform apply...", "🚀")
    slack = SlackNotifier()
    slack.send_initial_message("Starting Terraform apply...")

    try:
        # Initialize Terraform
        print_progress("Initializing Terraform...", "⚙️")
        slack.update_progress("Initializing Terraform...")
        run_command(["terraform", "init"])

        # Apply changes
        print_progress("Applying Terraform changes...", "🚀")
        slack.update_progress("Applying Terraform changes...")
        run_command(["terraform", "apply", "-auto-approve", "-no-color"])

        slack.update_progress("Terraform apply completed successfully.")

    except Exception as e:
        error_msg = str(e)
        print(f"❌ Error during Terraform apply: {error_msg}", file=sys.stderr)
        slack.send_error(error_msg)
        sys.exit(1)

    print_progress("Terraform apply completed successfully.", "✅")

if __name__ == "__main__":
    main() 