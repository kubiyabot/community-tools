import json
import os
import sys
import tempfile
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable
import re
import time

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
    location: str,
    plan_output: Optional[str] = None,
    workspace_url: Optional[str] = None,
    current_resource: Optional[str] = None,
    start_time: Optional[float] = None,
    error_message: Optional[str] = None,
    failed_step: Optional[int] = None
) -> List[Dict[str, Any]]:
    """Build enhanced Slack message blocks for deployment updates."""
    
    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": "⚡ Databricks Workspace Deployment",
                "emoji": True
            }
        },
        {
            "type": "section",
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": "*Deployment Details*"
                }
            ]
        },
        {
            "type": "section",
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": f"*Name*\n`{workspace_name}`"
                },
                {
                    "type": "mrkdwn",
                    "text": "*Provider*\n`Azure`"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Region*\n`{location}`"
                },
                {
                    "type": "mrkdwn",
                    "text": "*Mode*\n`terraform apply`"
                }
            ]
        }
    ]

    # If we have plan output, add the changes summary
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

        # Extract and format a sample of the most relevant resource changes
        resource_changes = []
        for line in plan_output.split('\n'):
            if any(x in line for x in ['+ resource', '~ resource', '- resource']):
                resource_changes.append(line)
        
        if resource_changes:
            # Get up to 3 most relevant changes
            sample_changes = '\n'.join(resource_changes[:3])
            # Add ellipsis if there are more changes
            if len(resource_changes) > 3:
                sample_changes += '\n...'

            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"```\nPlan: {adds} to add, {changes} to change, {destroys} to destroy.\n\n{sample_changes}```"
                }
            })

    # Add deployment progress section
    blocks.append({
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": ":rocket: *Deployment Progress*"
        }
    })

    # Define steps with their status
    steps = [
        ("Repository Cloning", 1),
        ("Terraform Init & Plan", 2),
        ("Infrastructure Apply", 3),
        ("Workspace Configuration", 4)
    ]

    # Add status for each step
    for step_name, step_num in steps:
        if failed_step and step_num == failed_step:
            # Failed step
            blocks.append({
                "type": "context",
                "elements": [{
                    "type": "mrkdwn",
                    "text": f":x: *Failed:* {step_name}"
                }]
            })
        elif step_num <= current_step and (status.startswith("✅") or status.startswith("❌")):
            # Completed step (when workflow is done)
            blocks.append({
                "type": "context",
                "elements": [{
                    "type": "mrkdwn",
                    "text": f":white_check_mark: *Completed:* {step_name}"
                }]
            })
        elif step_num < current_step:
            # Completed step (during workflow)
            blocks.append({
                "type": "context",
                "elements": [{
                    "type": "mrkdwn",
                    "text": f":white_check_mark: *Completed:* {step_name}"
                }]
            })
        elif step_num == current_step and not (status.startswith("✅") or status.startswith("❌")):
            # Current step - show spinner only if workflow is still in progress
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
            
            # If there's a current resource being created, show it
            if current_resource:
                blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"```Creating: {current_resource}```"
                    }
                })
        else:
            # Pending step (only show if not failed and not completed)
            if not failed_step and not status.startswith("✅"):
                blocks.append({
                    "type": "context",
                    "elements": [{
                        "type": "mrkdwn",
                        "text": f":hourglass_flowing_sand: *Pending:* {step_name}"
                    }]
                })

    # Add divider
    blocks.append({"type": "divider"})

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

    # Add progress indicator (only if not failed)
    if start_time and not failed_step:
        elapsed = int((time.time() - start_time) / 60)
        blocks.append({
            "type": "context",
            "elements": [{
                "type": "mrkdwn",
                "text": f":zap: *Progress:* Phase {current_step}/4 • :clock1: Started {elapsed}m ago"
            }]
        })

    # Add workspace URL and buttons if available
    if workspace_url:
        blocks.extend([
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*:link: Access Links*"
                }
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "🚀 Open Workspace",
                            "emoji": True
                        },
                        "url": workspace_url,
                        "style": "primary"
                    },
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "📦 Terraform Backend",
                            "emoji": True
                        },
                        "url": f"https://portal.azure.com/#@/resource/subscriptions/{os.environ['ARM_SUBSCRIPTION_ID']}/resourceGroups/{os.environ['RESOURCE_GROUP_NAME']}/providers/Microsoft.Storage/storageAccounts/{os.environ['STORAGE_ACCOUNT_NAME']}/overview"
                    }
                ]
            }
        ])

    return blocks

def print_progress(message: str, emoji: str) -> None:
    """Print progress messages with emoji."""
    print(f"\n{emoji} {message}", flush=True)
    sys.stdout.flush()

def run_command(
    cmd: List[str],
    cwd: Optional[str] = None,
    capture_output: bool = False,
    stream_output: bool = False,
    callback: Optional[Callable[[str], None]] = None
) -> Optional[str]:
    """Run a command with proper error handling and output control."""
    print_progress(f"Running command: {' '.join(cmd)}", "🔄")
    
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
                env=env
            )
            print(result.stdout, flush=True)
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
            
            output_buffer = []
            while True:
                line = process.stdout.readline()
                if not line and process.poll() is not None:
                    break
                if line:
                    output_buffer.append(line.rstrip())
                    if callback:
                        callback(line.rstrip())
                    print(line.rstrip(), flush=True)
                    sys.stdout.flush()
            
            if process.returncode != 0:
                error_msg = "\n".join(output_buffer[-10:])
                raise subprocess.CalledProcessError(process.returncode, cmd, error_msg)
        else:
            # For non-captured output, use subprocess.run with real-time output
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
            
            while True:
                line = process.stdout.readline()
                if not line and process.poll() is not None:
                    break
                if line:
                    print(line.rstrip(), flush=True)
                    sys.stdout.flush()
            
            if process.returncode != 0:
                raise subprocess.CalledProcessError(process.returncode, cmd)
        
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr if hasattr(e, 'stderr') and e.stderr else str(e)
        print(f"❌ Command failed: {' '.join(cmd)}\n{error_msg}", file=sys.stderr, flush=True)
        raise RuntimeError(f"Command failed: {' '.join(cmd)}\n{error_msg}")

class SlackNotifier:
    def __init__(self):
        """Initialize Slack client with error handling and timing."""
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

    def update_progress(
        self,
        status: str,
        message: str,
        current_step: int,
        plan_output: Optional[str] = None,
        workspace_url: Optional[str] = None,
        current_resource: Optional[str] = None,
        start_time: Optional[float] = None,
        is_complete: bool = False,
        error_message: Optional[str] = None,
        failed_step: Optional[int] = None
    ) -> None:
        """Enhanced progress update with error handling."""
        if not self.enabled:
            return

        try:
            blocks = build_message_blocks(
                status=status,
                message=message,
                current_step=current_step,
                workspace_name=os.environ["WORKSPACE_NAME"],
                location=os.environ["LOCATION"],
                plan_output=plan_output,
                workspace_url=workspace_url,
                current_resource=current_resource,
                start_time=start_time or self.start_time,
                error_message=error_message,
                failed_step=failed_step
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
        """Send error message and update UI to reflect failure."""
        if not self.enabled:
            return

        try:
            # Update the progress UI to show failure
            self.update_progress(
                status="❌ Deployment Failed",
                message="Deployment failed due to an error",
                current_step=4,  # Set to current step when error occurred
                error_message=error_message,
                failed_step=3,  # Mark the current step as failed
                start_time=self.start_time
            )
        except Exception as e:
            print(f"Warning: Failed to send error message to Slack: {str(e)}")
            self.enabled = False

def create_tfvars(args: Dict[str, Any], tfvars_path: Path) -> None:
    """Create terraform.tfvars.json file from arguments"""
    # Sanitize the workspace_name
    sanitized_workspace_name = re.sub(r"[^a-zA-Z0-9()._-]", "", os.environ["WORKSPACE_NAME"])

    tfvars = {
        "workspace_name": sanitized_workspace_name,
        "location": os.environ['LOCATION'],
        "managed_services_cmk_key_vault_key_id": os.environ.get("managed_services_cmk_key_vault_key_id"),
        "managed_disk_cmk_key_vault_key_id": os.environ.get("managed_disk_cmk_key_vault_key_id"), 
        "infrastructure_encryption_enabled": os.environ.get("infrastructure_encryption_enabled") == "true",
        "no_public_ip": os.environ.get("no_public_ip") == "true",
        "enable_vnet": os.environ.get("enable_vnet") == "true",
        "virtual_network_id": os.environ.get("virtual_network_id"),
        "private_subnet_name": os.environ.get("private_subnet_name"),
        "public_subnet_name": os.environ.get("public_subnet_name"),
        # Remove None values
        **{k: v for k, v in args.items() if v is not None and k not in {
            "workspace_name", "region", "storage_account_name", 
            "container_name", "resource_group_name"
        }}
    }
    with open(tfvars_path, 'w') as f:
        json.dump(tfvars, f, indent=2)

def handle_terraform_output(line: str, slack: 'SlackNotifier', start_time: float) -> None:
    """Enhanced handler for Terraform output lines."""
    print(line, flush=True)
    if "Creating..." in line:
        match = re.search(r'(\S+): Creating\.\.\.', line)
        if match:
            resource = match.group(1)
            slack.update_progress(
                status="🚀 Deploying Resources",
                message="Applying infrastructure changes",
                current_step=3,
                current_resource=resource,
                start_time=start_time
            )
    elif "Error:" in line or "Error applying plan:" in line:
        slack.update_progress(
            status="❌ Deployment Failed",
            message="Error during resource creation",
            current_step=3,
            start_time=start_time,
            error_message=line,
            failed_step=3
        )
    elif "Apply complete!" in line:
        slack.update_progress(
            status="✅ Deployment Successful",
            message="All resources have been successfully created",
            current_step=4,
            start_time=start_time,
            is_complete=True
        )

def main():
    print_progress("All checks passed, starting deployment...", "✅")
    
    if len(sys.argv) != 2:
        print("Usage: deploy_to_azure.py <tfvars_file>", file=sys.stderr)
        sys.exit(1)

    # Read tfvars file
    tfvars_file = Path(sys.argv[1])
    print_progress(f"Reading tfvars file: {tfvars_file}", "📄")
    
    try:
        with open(tfvars_file) as f:
            tfvars = json.load(f)
            print_progress("Successfully loaded tfvars", "✅")
    except Exception as e:
        print(f"❌ Failed to read tfvars file: {str(e)}", file=sys.stderr)
        sys.exit(1)

    # print the TFVARS
    print_progress("TFVARS:", "📄")
    print(tfvars)

    # Print environment variables for debugging (excluding sensitive data)
    print_progress("Environment variables:", "🔍")
    safe_vars = ["WORKSPACE_NAME", "LOCATION", "STORAGE_ACCOUNT_NAME", "CONTAINER_NAME", "RESOURCE_GROUP_NAME"]
    for var in safe_vars:
        print(f"  {var}: {os.environ.get(var, 'NOT SET')}")

    # Get required values from environment variables
    required_vars = [
        "WORKSPACE_NAME",
        "LOCATION",
        "STORAGE_ACCOUNT_NAME",
        "CONTAINER_NAME",
        "RESOURCE_GROUP_NAME",
        "ARM_SUBSCRIPTION_ID"
    ]

    for var in required_vars:
        if var not in os.environ or not os.environ[var]:
            print(f"❌ Required environment variable {var} is not set")
            sys.exit(1)

    # Set workspace name and location from environment
    os.environ["WORKSPACE_NAME"] = os.environ["WORKSPACE_NAME"]
    os.environ["LOCATION"] = os.environ["LOCATION"]

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
            f"resource_group_name={os.environ['WORKSPACE_NAME']}"
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
        
        # Keep the plan visible throughout the deployment
        slack.update_progress(
            status="📋 Terraform Plan Generated",
            message="Reviewing changes to be made...",
            current_step=2,
            plan_output=plan_output
        )

        # The plan summary will now stay visible in subsequent updates
        print_progress("Applying Terraform configuration...", "🚀")
        run_command(
            ["terraform", "apply", "-auto-approve", "-var-file=terraform.tfvars.json", "-no-color"],
            cwd=tf_dir,
            stream_output=True,
            callback=lambda line: handle_terraform_output(line, slack, time.time())
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
        slack.update_progress(
            status="❌ Deployment Failed",
            message=str(e),
            current_step=4
        )
        sys.exit(1)

    finally:
        # Cleanup
        print_progress("Cleaning up workspace...", "🧹")
        import shutil
        shutil.rmtree(workspace_dir, ignore_errors=True)

if __name__ == "__main__":
    main() 