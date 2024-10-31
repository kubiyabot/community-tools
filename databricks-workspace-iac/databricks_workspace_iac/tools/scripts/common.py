import json
import os
import subprocess
import sys
from typing import Optional, Dict, List, Callable, Any
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from databricks_workspace_iac.tools.templates.slack_blocks import build_message_blocks

def print_progress(message: str, emoji: str) -> None:
    """Print progress messages with emoji."""
    print(f"\n{emoji} {message}", flush=True)

def run_command(
    cmd: List[str],
    cwd: Optional[str] = None,
    capture_output: bool = False,
    stream_output: bool = False,
    callback: Optional[Callable[[str], None]] = None
) -> Optional[str]:
    """Run a command with proper error handling and output control."""
    try:
        if capture_output:
            result = subprocess.run(
                cmd,
                cwd=cwd,
                check=True,
                capture_output=True,
                text=True
            )
            return result.stdout
        elif stream_output:
            process = subprocess.Popen(
                cmd,
                cwd=cwd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            while True:
                line = process.stdout.readline()
                if not line and process.poll() is not None:
                    break
                if line:
                    if callback:
                        callback(line.rstrip())
                    else:
                        print(line.rstrip(), flush=True)
            
            if process.returncode != 0:
                raise subprocess.CalledProcessError(process.returncode, cmd)
        else:
            subprocess.run(cmd, cwd=cwd, check=True)
        
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr if e.stderr else str(e)
        raise RuntimeError(f"Command failed: {' '.join(cmd)}\n{error_msg}")

class SlackNotifier:
    def __init__(self):
        """Initialize Slack client with error handling."""
        try:
            self.client = WebClient(token=os.environ["SLACK_API_TOKEN"])
            self.channel = os.environ["SLACK_CHANNEL_ID"]
        except KeyError as e:
            raise RuntimeError(f"Missing required environment variable: {e}")
        
        self.message_ts = None
        self.thread_ts = os.environ.get("SLACK_THREAD_TS")

    def send_initial_message(self, text: str) -> None:
        """Send initial message and store timestamp."""
        try:
            response = self.client.chat_postMessage(
                channel=self.channel,
                text=text,
                thread_ts=self.thread_ts
            )
            self.message_ts = response["ts"]
        except SlackApiError as e:
            print(f"⚠️ Failed to send initial Slack message: {e.response['error']}", file=sys.stderr)
            raise

    def update_progress(
        self,
        status: str,
        message: str,
        phase: str,
        plan_output: Optional[str] = None,
        workspace_url: Optional[str] = None
    ) -> None:
        """Update progress message with rich formatting."""
        try:
            blocks = build_message_blocks(
                status=status,
                message=message,
                phase=phase,
                workspace_name=os.environ["WORKSPACE_NAME"],
                region=os.environ["REGION"],
                plan_output=plan_output,
                workspace_url=workspace_url
            )

            self.client.chat_update(
                channel=self.channel,
                ts=self.message_ts,
                blocks=blocks
            )

        except SlackApiError as e:
            print(f"⚠️ Failed to update Slack message: {e.response['error']}", file=sys.stderr)

    def send_error(self, error_message: str) -> None:
        """Send error message with proper formatting."""
        try:
            blocks = [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "❌ Deployment Failed",
                        "emoji": True
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Error:*\n```{error_message}```"
                    }
                }
            ]

            if self.message_ts:
                self.client.chat_update(
                    channel=self.channel,
                    ts=self.message_ts,
                    blocks=blocks
                )
            else:
                self.client.chat_postMessage(
                    channel=self.channel,
                    thread_ts=self.thread_ts,
                    blocks=blocks
                )

        except SlackApiError as e:
            print(f"⚠️ Failed to send error message to Slack: {e.response['error']}", file=sys.stderr)