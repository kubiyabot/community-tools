import os
import sys
import json
import time
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional, List

try:
    from slack_sdk import WebClient
    from slack_sdk.errors import SlackApiError
    SLACK_AVAILABLE = True
except ImportError:
    SLACK_AVAILABLE = False
    print("Warning: slack_sdk not available. Slack notifications will be disabled.")

def build_message_blocks(
    status: str,
    message: str,
    current_step: int,
    module_name: str,
    source: str,
    plan_output: Optional[str] = None,
    current_resource: Optional[str] = None,
    start_time: Optional[float] = None,
    error_message: Optional[str] = None,
    failed_step: Optional[int] = None
) -> Dict[str, Any]:
    """Build Slack message blocks for terraform updates."""
    
    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": "⚡ Terraform Module Operation",
                "emoji": True
            }
        },
        {
            "type": "section",
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": "*Module Details*"
                }
            ]
        },
        {
            "type": "section",
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": f"*Name*\n`{module_name}`"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Source*\n`{source}`"
                }
            ]
        }
    ]

    # Add plan output if available
    if plan_output:
        # Parse plan output to get resource counts
        add_count = re.search(r'Plan: (\d+) to add', plan_output)
        change_count = re.search(r'(\d+) to change', plan_output)
        destroy_count = re.search(r'(\d+) to destroy', plan_output)
        
        adds = add_count.group(1) if add_count else "0"
        changes = change_count.group(1) if change_count else "0"
        destroys = destroy_count.group(1) if destroy_count else "0"

        blocks.append({
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f":bar_chart: Changes Summary: `+{adds}` new | `~{changes}` modified | `-{destroys}` removed"
                }
            ]
        })

        # Extract and format resource changes
        resource_changes = []
        for line in plan_output.split('\n'):
            if any(x in line for x in ['+ resource', '~ resource', '- resource']):
                resource_changes.append(line)
        
        if resource_changes:
            sample_changes = '\n'.join(resource_changes[:3])
            if len(resource_changes) > 3:
                sample_changes += '\n...'

            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"```\n{sample_changes}```"
                }
            })

    # Add progress section
    blocks.append({
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": ":rocket: *Operation Progress*"
        }
    })

    # Define steps
    steps = [
        ("Module Initialization", 1),
        ("Terraform Plan", 2),
        ("Infrastructure Apply", 3),
        ("Validation", 4)
    ]

    # Add status for each step
    for step_name, step_num in steps:
        if failed_step and step_num == failed_step:
            blocks.append({
                "type": "context",
                "elements": [{
                    "type": "mrkdwn",
                    "text": f":x: *Failed:* {step_name}"
                }]
            })
        elif step_num <= current_step and status.startswith("✅"):
            blocks.append({
                "type": "context",
                "elements": [{
                    "type": "mrkdwn",
                    "text": f":white_check_mark: *Completed:* {step_name}"
                }]
            })
        elif step_num < current_step:
            blocks.append({
                "type": "context",
                "elements": [{
                    "type": "mrkdwn",
                    "text": f":white_check_mark: *Completed:* {step_name}"
                }]
            })
        elif step_num == current_step:
            blocks.append({
                "type": "context",
                "elements": [
                    {
                        "type": "image",
                        "image_url": "https://kubiya-public-20221113173935726800000003.s3.us-east-1.amazonaws.com/spinner.gif",
                        "alt_text": "in progress"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*In Progress:* {message}"
                    }
                ]
            })
            
            if current_resource:
                blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"```Creating: {current_resource}```"
                    }
                })

    # Add error message if present
    if error_message:
        blocks.extend([
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*:warning: Error Details*"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"```{error_message}```"
                }
            }
        ])

    # Add elapsed time if available
    if start_time:
        elapsed = int((time.time() - start_time) / 60)
        blocks.append({
            "type": "context",
            "elements": [{
                "type": "mrkdwn",
                "text": f":zap: *Progress:* Phase {current_step}/4 • :clock1: Started {elapsed}m ago"
            }]
        })

    return {"blocks": blocks}

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
            print(f"Warning: Missing Slack environment variable: {e}")
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

    def update_progress(
        self,
        status: str,
        message: str,
        current_step: int,
        module_name: str,
        source: str,
        plan_output: Optional[str] = None,
        current_resource: Optional[str] = None,
        error_message: Optional[str] = None,
        failed_step: Optional[int] = None
    ) -> None:
        """Update progress message with current status."""
        if not self.enabled:
            return

        try:
            blocks = build_message_blocks(
                status=status,
                message=message,
                current_step=current_step,
                module_name=module_name,
                source=source,
                plan_output=plan_output,
                current_resource=current_resource,
                start_time=self.start_time,
                error_message=error_message,
                failed_step=failed_step
            )

            self.client.chat_update(
                channel=self.channel,
                ts=self.message_ts,
                blocks=blocks["blocks"]
            )
        except Exception as e:
            print(f"Warning: Failed to update Slack message: {str(e)}")
            self.enabled = False

def run_command(
    cmd: List[str],
    cwd: Optional[str] = None,
    capture_output: bool = False,
    stream_output: bool = False,
    env: Optional[Dict[str, str]] = None
) -> Optional[str]:
    """Run a command with proper error handling and output control."""
    try:
        if capture_output:
            result = subprocess.run(
                cmd,
                cwd=cwd,
                check=True,
                capture_output=True,
                text=True,
                env=env
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
                universal_newlines=True,
                env=env
            )
            
            output = []
            while True:
                line = process.stdout.readline()
                if not line and process.poll() is not None:
                    break
                if line:
                    output.append(line.rstrip())
                    print(line.rstrip(), flush=True)
            
            if process.returncode != 0:
                error_msg = "\n".join(output[-10:])
                raise subprocess.CalledProcessError(process.returncode, cmd, error_msg)
            
            return "\n".join(output)
        else:
            subprocess.run(cmd, cwd=cwd, check=True, env=env)
            return None

    except subprocess.CalledProcessError as e:
        error_msg = e.stderr if hasattr(e, 'stderr') and e.stderr else str(e)
        raise RuntimeError(f"Command failed: {' '.join(cmd)}\n{error_msg}")

def handle_terraform_output(line: str, slack: SlackNotifier, module_name: str, source: str) -> None:
    """Process Terraform output and update status."""
    print(line, flush=True)
    
    if "Creating..." in line:
        match = re.search(r'(\S+): Creating\.\.\.', line)
        if match:
            resource = match.group(1)
            slack.update_progress(
                status="🚀 Applying Changes",
                message="Creating resources...",
                current_step=3,
                module_name=module_name,
                source=source,
                current_resource=resource
            )
    elif "Error:" in line or "Error applying plan:" in line:
        slack.update_progress(
            status="❌ Operation Failed",
            message="Error during resource creation",
            current_step=3,
            module_name=module_name,
            source=source,
            error_message=line,
            failed_step=3
        )
    elif "Apply complete!" in line:
        slack.update_progress(
            status="✅ Operation Successful",
            message="All resources have been created",
            current_step=4,
            module_name=module_name,
            source=source
        )

def main():
    if len(sys.argv) != 3:
        print("Usage: terraform_handler.py <module_config> <variables>")
        sys.exit(1)

    module_config = json.loads(sys.argv[1])
    variables = json.loads(sys.argv[2])
    
    slack = SlackNotifier()
    slack.send_initial_message("Starting Terraform operation...")

    try:
        # Initialize Terraform
        slack.update_progress(
            status="🔄 Initializing",
            message="Setting up Terraform...",
            current_step=1,
            module_name=module_config["name"],
            source=module_config["source"]
        )
        
        run_command(["terraform", "init"])

        # Generate plan
        slack.update_progress(
            status="📋 Planning",
            message="Calculating changes...",
            current_step=2,
            module_name=module_config["name"],
            source=module_config["source"]
        )
        
        plan_output = run_command(
            ["terraform", "plan", "-no-color"],
            capture_output=True
        )
        
        slack.update_progress(
            status="✅ Plan Generated",
            message="Reviewing changes...",
            current_step=2,
            module_name=module_config["name"],
            source=module_config["source"],
            plan_output=plan_output
        )

        # Apply changes
        slack.update_progress(
            status="🚀 Applying",
            message="Making changes...",
            current_step=3,
            module_name=module_config["name"],
            source=module_config["source"]
        )
        
        apply_output = run_command(
            ["terraform", "apply", "-auto-approve", "-no-color"],
            stream_output=True
        )
        
        # Final success message
        slack.update_progress(
            status="✅ Success",
            message="Operation completed successfully",
            current_step=4,
            module_name=module_config["name"],
            source=module_config["source"]
        )

    except Exception as e:
        error_msg = str(e)
        print(f"Error: {error_msg}", file=sys.stderr)
        slack.update_progress(
            status="❌ Failed",
            message="Operation failed",
            current_step=4,
            module_name=module_config["name"],
            source=module_config["source"],
            error_message=error_msg
        )
        sys.exit(1)

if __name__ == "__main__":
    main() 