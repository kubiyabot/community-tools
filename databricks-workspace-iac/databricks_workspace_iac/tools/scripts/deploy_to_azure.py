import json
import os
import sys
import tempfile
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable
import re

# At the top of the file, modify the imports to handle missing slack_sdk
try:
    from slack_sdk import WebClient
    from slack_sdk.errors import SlackApiError
    SLACK_AVAILABLE = True
except ImportError:
    SLACK_AVAILABLE = False
    print("Warning: slack_sdk not available. Slack notifications will be disabled.")

# Include the build_message_blocks function directly in this file
def build_message_blocks(
    status: str,
    message: str,
    current_step: int,
    workspace_name: str,
    region: str,
    plan_output: Optional[str] = None,
    workspace_url: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Build Slack message blocks for deployment updates."""
    steps = [
        "1️⃣ Preparing to create workspace",
        "2️⃣ Initializing Terraform and generating plan",
        "3️⃣ Applying Terraform configuration",
        "4️⃣ Finalizing deployment"
    ]

    # Mark completed steps with a checkmark
    for i in range(len(steps)):
        if i < current_step - 1:
            steps[i] = f"✅ {steps[i]}"
        elif i == current_step - 1:
            steps[i] = f"> *{steps[i]}*"  # Highlight current step

    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": status,
                "emoji": True
            }
        },
        {
            "type": "section",
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": f"*Workspace:*\n{workspace_name}"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Region:*\n{region}"
                }
            ]
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": message
            }
        },
        {
            "type": "divider"
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*Deployment Progress:*"
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "\n".join(steps)
            }
        }
    ]

    if plan_output:
        # Truncate plan_output to avoid exceeding Slack's message size limit
        max_length = 2900  # Slack block text limit is 3000 characters
        if len(plan_output) > max_length:
            plan_output = plan_output[:max_length] + "\n...(truncated)..."
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Terraform Plan Output:*\n```{plan_output}```"
            }
        })
    
    if workspace_url:
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Workspace URL:* {workspace_url}"
            }
        })

    return blocks

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
    # Set TF_IN_AUTOMATION environment variable to disable color codes
    env = os.environ.copy()
    env["TF_IN_AUTOMATION"] = "1"

    try:
        if capture_output:
            result = subprocess.run(
                cmd,
                cwd=cwd,
                check=True,
                capture_output=True,
                text=True,
                env=env  # Pass the modified environment
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
                env=env  # Pass the modified environment
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
            subprocess.run(cmd, cwd=cwd, check=True, env=env)
        
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr if e.stderr else str(e)
        raise RuntimeError(f"Command failed: {' '.join(cmd)}\n{error_msg}")

class SlackNotifier:
    def __init__(self):
        """Initialize Slack client with error handling."""
        self.enabled = SLACK_AVAILABLE
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

    def update_progress(
        self,
        status: str,
        message: str,
        current_step: int,
        plan_output: Optional[str] = None,
        workspace_url: Optional[str] = None
    ) -> None:
        """Update progress message with rich formatting."""
        if not self.enabled:
            return

        try:
            blocks = build_message_blocks(
                status=status,
                message=message,
                current_step=current_step,
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
        except Exception as e:
            print(f"Warning: Failed to update Slack message: {str(e)}")
            self.enabled = False

    def send_error(self, error_message: str) -> None:
        """Send error message with proper formatting."""
        if not self.enabled:
            return

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
        except Exception as e:
            print(f"Warning: Failed to send error message to Slack: {str(e)}")
            self.enabled = False

def create_tfvars(args: Dict[str, Any], tfvars_path: Path) -> None:
    """Create terraform.tfvars.json file from arguments"""
    # Sanitize the workspace_name
    sanitized_workspace_name = re.sub(r"[^a-zA-Z0-9()._-]", "", args["workspace_name"])

    tfvars = {
        "workspace_name": sanitized_workspace_name,
        "location": args["location"],
        "managed_services_cmk_key_vault_key_id": args.get("managed_services_cmk_key_vault_key_id"),
        "managed_disk_cmk_key_vault_key_id": args.get("managed_disk_cmk_key_vault_key_id"),
        "infrastructure_encryption_enabled": args.get("infrastructure_encryption_enabled") == "true",
        "no_public_ip": args.get("no_public_ip") == "true",
        "enable_vnet": args.get("enable_vnet") == "true",
        "virtual_network_id": args.get("virtual_network_id"),
        "private_subnet_name": args.get("private_subnet_name"),
        "public_subnet_name": args.get("public_subnet_name"),
        # Remove None values
        **{k: v for k, v in args.items() if v is not None and k not in {
            "workspace_name", "region", "storage_account_name", 
            "container_name", "resource_group_name"
        }}
    }
    
    with open(tfvars_path, 'w') as f:
        json.dump(tfvars, f, indent=2)

def handle_terraform_output(line: str, slack: 'SlackNotifier') -> None:
    """Handle and parse Terraform output lines."""
    print(line, flush=True)
    if "Creating..." in line:
        # Extract resource name safely using regex
        match = re.search(r'(\S+): Creating\.\.\.', line)
        if match:
            resource = match.group(1)
            slack.update_progress(
                status="🚀 Deploying Resources",
                message=f"Creating resource: `{resource}`",
                current_step=3
            )
    elif "Apply complete!" in line:
        slack.update_progress(
            status="✅ Resources Deployed",
            message="All resources have been successfully created",
            current_step=4
        )

def main():
    if len(sys.argv) != 2:
        print("Usage: deploy_to_azure.py <tfvars_file>")
        sys.exit(1)

    # Read tfvars file
    tfvars_file = Path(sys.argv[1])
    with open(tfvars_file) as f:
        tfvars = json.load(f)

    # Get required values from environment variables
    required_vars = [
        "WORKSPACE_NAME",
        "REGION",
        "STORAGE_ACCOUNT_NAME",
        "CONTAINER_NAME",
        "RESOURCE_GROUP_NAME"
    ]
    
    for var in required_vars:
        if var not in os.environ:
            print(f"❌ Required environment variable {var} is not set")
            sys.exit(1)

    # Set workspace name and region from environment
    os.environ["WORKSPACE_NAME"] = os.environ["WORKSPACE_NAME"]
    os.environ["REGION"] = os.environ["REGION"]

    # Set up workspace
    workspace_dir = Path(tempfile.mkdtemp())
    slack = SlackNotifier()

    try:
        # Initial Slack message
        print_progress("Starting Databricks Workspace deployment...", "🚀")
        slack.send_initial_message("Initializing Databricks Workspace deployment...")
        slack.update_progress(
            status="🚀 Deployment Started",
            message="Preparing to create workspace...",
            current_step=1
        )

        # Clone repository
        print_progress("Cloning Infrastructure Repository...", "📦")
        repo_dir = workspace_dir / "repo"
        # Clone repository
        clone_cmd = [
            "git", "clone",
            f"https://{os.environ['PAT']}@github.com/{os.environ['GIT_ORG']}/{os.environ['GIT_REPO']}.git",
            str(repo_dir)
        ]
        run_command(clone_cmd)

        # Checkout specific branch if specified
        if 'BRANCH' in os.environ:
            print_progress(f"Checking out branch: {os.environ['BRANCH']}", "🔄")
            run_command(["git", "checkout", os.environ['BRANCH']], cwd=repo_dir)
        slack.update_progress(
            status="📦 Repository Cloned",
            message="Infrastructure repository cloned successfully",
            current_step=2
        )

        # Navigate to terraform directory
        tf_dir = repo_dir / "aux/databricks/terraform/azure"
        if not tf_dir.exists():
            raise RuntimeError(f"Terraform directory not found at expected location: {tf_dir}")
            
        # Create terraform.tfvars.json file in the terraform directory
        create_tfvars(tfvars, tf_dir / "terraform.tfvars.json")

        # Initialize Terraform
        print_progress("Initializing Terraform...", "⚙️")
        backend_config = [
            f"storage_account_name={os.environ['STORAGE_ACCOUNT_NAME']}",
            f"container_name={os.environ['CONTAINER_NAME']}",
            f"key=databricks/{os.environ['WORKSPACE_NAME']}/terraform.tfstate",
            f"resource_group_name={os.environ['RESOURCE_GROUP_NAME']}",
            f"subscription_id={os.environ['ARM_SUBSCRIPTION_ID']}"
        ]
        
        run_command(
            ["terraform", "init", "-no-color"] + [f"-backend-config={c}" for c in backend_config],
            cwd=tf_dir
        )
        slack.update_progress(
            status="⚙️ Terraform Initialized",
            message="Terraform successfully initialized",
            current_step=2
        )

        # Generate and show plan
        print_progress("Generating Terraform plan...", "📋")
        plan_output = run_command(
            ["terraform", "plan", "-var-file=terraform.tfvars.json", "-no-color"],
            cwd=tf_dir,
            capture_output=True
        )
        slack.update_progress(
            status="📋 Terraform Plan Generated",
            message="Reviewing changes to be made...",
            current_step=2,
            plan_output=plan_output
        )

        # Apply Terraform
        print_progress("Applying Terraform configuration...", "🚀")
        run_command(
            ["terraform", "apply", "-auto-approve", "-var-file=terraform.tfvars.json", "-no-color"],
            cwd=tf_dir,
            stream_output=True,
            callback=lambda line: handle_terraform_output(line, slack)
        )

        # Get workspace URL
        workspace_url = run_command(
            ["terraform", "output", "-raw", "databricks_host"],
            cwd=tf_dir,
            capture_output=True
        )
        workspace_url = f"https://{workspace_url.strip()}"

        # Final success message
        print_progress(f"Workspace URL: {workspace_url}", "🔗")
        slack.update_progress(
            status="✅ Deployment Successful",
            message=f"Databricks workspace *{os.environ['WORKSPACE_NAME']}* has been successfully provisioned!",
            current_step=4,
            workspace_url=workspace_url
        )

    except Exception as e:
        print(f"\n❌ Error: {str(e)}", file=sys.stderr)
        slack.send_error(str(e))
        slack.update_progress("❌ Deployment Failed", str(e), "4")
        sys.exit(1)

    finally:
        # Cleanup
        print_progress("Cleaning up workspace...", "🧹")
        import shutil
        shutil.rmtree(workspace_dir, ignore_errors=True)

if __name__ == "__main__":
    main() 