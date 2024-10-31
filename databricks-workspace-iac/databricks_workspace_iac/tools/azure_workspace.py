from typing import Optional, Dict, List
from kubiya_sdk.tools import function_tool
from kubiya_sdk.tools.models import FileSpec
import pathlib

# Read the Slack templates JSON file
current_dir = pathlib.Path(__file__).parent
with open(current_dir / "templates" / "slack_templates.json", "r") as f:
    slack_templates_content = f.read()

@function_tool(
    description="Create a Databricks workspace on Azure using Infrastructure as Code (Terraform).",
    requirements=[
        "slack_sdk>=3.19.0"
    ],
   # long_running=True,
   # icon_url="https://raw.githubusercontent.com/databricks/databricks-sdk-py/main/docs/_static/databricks-icon.png",
   # with_files=[
   #     FileSpec(
   #         destination="/tmp/slack_templates.json",
   #         content=slack_templates_content,
   #     )
   # ],
   # mermaid="""
   # sequenceDiagram
   #     participant U as User 👤
   #     participant S as System 🖥️
   #     participant T as Terraform ⚙️
   #     participant A as Azure ☁️
   #     participant D as Databricks 🚀

    #    U ->> S: Start Deployment 🎬
    #    S ->> T: Initialize Terraform
    #    T ->> A: Request resources 🏗️
    #    A -->> T: Resources provisioned ✅
    #    T ->> D: Configure workspace 🔧
    #    D -->> T: Workspace ready 🌟
    #    S -->> U: Success! Here's your workspace URL 🎉
    #"""
)
def create_databricks_workspace(
    workspace_name: str,
    region: str,
    storage_account_name: str,
    container_name: str,
    resource_group_name: str,
    # Network Configuration
    enable_vnet: bool = False,
    virtual_network_id: Optional[str] = None,
    private_subnet_name: Optional[str] = None,
    public_subnet_name: Optional[str] = None,
    public_subnet_network_security_group_association_id: Optional[str] = None,
    private_subnet_network_security_group_association_id: Optional[str] = None,
    no_public_ip: bool = False,
    # Security Configuration
    managed_services_cmk_key_vault_key_id: Optional[str] = None,
    managed_disk_cmk_key_vault_key_id: Optional[str] = None,
    infrastructure_encryption_enabled: bool = False,
    security_profile_enabled: bool = False,
    # Monitoring Configuration
    enhanced_monitoring_enabled: bool = False,
    # Update Configuration
    automatic_update: bool = False,
    restart_no_updates: bool = False,
    day_of_week: Optional[str] = None,
    frequency: Optional[str] = None,
    hours: int = 1,
    minutes: int = 0,
    # Network CIDR Configuration
    address_space: List[str] = ["10.0.0.0/16"],
    address_prefixes_public: List[str] = ["10.0.2.0/24"],
    address_prefixes_private: List[str] = ["10.0.1.0/24"],
    # Tags
    tags: Optional[Dict[str, str]] = None
) -> str:
    """Create a Databricks workspace on Azure using Infrastructure as Code (Terraform)."""
    # Import required packages inside the function
    import json
    import os
    import sys
    import tempfile
    from pathlib import Path
    import subprocess
    from slack_sdk import WebClient
    from slack_sdk.errors import SlackApiError
    from typing import List, Callable

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
                result = subprocess.run(cmd, cwd=cwd, check=True, capture_output=True, text=True)
                return result.stdout
            elif stream_output:
                process = subprocess.Popen(
                    cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                    text=True, bufsize=1, universal_newlines=True
                )
                while True:
                    line = process.stdout.readline()
                    if not line and process.poll() is not None:
                        break
                    if line and callback:
                        callback(line.rstrip())
                if process.returncode != 0:
                    raise subprocess.CalledProcessError(process.returncode, cmd)
            else:
                subprocess.run(cmd, cwd=cwd, check=True)
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr if e.stderr else str(e)
            raise RuntimeError(f"Command failed: {' '.join(cmd)}\n{error_msg}")

    def load_slack_templates() -> Dict:
        """Load Slack block templates from JSON file"""
        with open("/tmp/slack_templates.json", "r") as f:
            return json.load(f)

    def update_status(message: str, emoji: str = "ℹ️", phase: str = None) -> None:
        """Update both console and Slack with progress"""
        print(f"\n{emoji} {message}", flush=True)
        if slack and message_ts:
            try:
                templates = load_slack_templates()
                blocks = templates["status_update"]["blocks"]
                
                # Replace template variables
                for block in blocks:
                    if "${status}" in str(block):
                        block["text"]["text"] = f"{emoji} {current_phase}"
                    if "${message}" in str(block):
                        block["text"]["text"] = message
                    if "${phase}" in str(block):
                        block["elements"][1]["text"] = f"*Phase {phase or current_step} of 7* • Databricks Workspace Deployment"
                    if "${workspace_name}" in str(block):
                        block["fields"][0]["text"] = f"*Workspace:*\n`{workspace_name}`"
                    if "${region}" in str(block):
                        block["fields"][1]["text"] = f"*Region:*\n`{region}`"
                
                if workspace_url and 'workspace_url' in locals():
                    blocks.append(templates["workspace_button"])
                    blocks[-1]["elements"][0]["url"] = workspace_url

                slack.chat_update(
                    channel=channel_id,
                    ts=message_ts,
                    blocks=blocks
                )
            except Exception as e:
                print(f"⚠️ Failed to update Slack: {str(e)}", file=sys.stderr)

    # Initialize variables
    current_step = 1
    current_phase = "Initializing"
    workspace_url = None
    
    # Initialize Slack client
    slack = WebClient(token=os.environ["SLACK_API_TOKEN"])
    channel_id = os.environ["SLACK_CHANNEL_ID"]
    message_ts = None

    # Create temporary directory
    workspace_dir = Path(tempfile.mkdtemp())
    
    try:
        # Send initial message
        current_phase = "Starting Deployment"
        response = slack.chat_postMessage(
            channel=channel_id,
            text="🚀 Starting Databricks Workspace deployment..."
        )
        message_ts = response["ts"]
        update_status("Preparing deployment environment")

        # Clone repository
        current_step = 2
        current_phase = "Cloning Repository"
        update_status("Cloning Infrastructure Repository", "📦")
        repo_dir = workspace_dir / "repo"
        run_command([
            "git", "clone",
            f"https://{os.environ['PAT']}@github.com/{os.environ['GIT_ORG']}/{os.environ['GIT_REPO']}.git",
            str(repo_dir)
        ])

        # Create terraform.tfvars.json
        current_step = 3
        current_phase = "Preparing Terraform"
        update_status("Creating Terraform configuration", "⚙️")
        tf_dir = repo_dir / "aux/databricks/terraform/azure"
        tfvars_path = tf_dir / "terraform.tfvars.json"
        
        # Create tfvars with all supported parameters
        tfvars = {
            # Basic Configuration
            "workspace_name": workspace_name,
            "location": region,
            
            # Network Configuration
            "enable_vnet": enable_vnet,
            "no_public_ip": no_public_ip,
            "virtual_network_id": virtual_network_id,
            "private_subnet_name": private_subnet_name,
            "public_subnet_name": public_subnet_name,
            "public_subnet_network_security_group_association_id": public_subnet_network_security_group_association_id,
            "private_subnet_network_security_group_association_id": private_subnet_network_security_group_association_id,
            "address_space": address_space,
            "address_prefixes_public": address_prefixes_public,
            "address_prefixes_private": address_prefixes_private,
            
            # Security Configuration
            "managed_services_cmk_key_vault_key_id": managed_services_cmk_key_vault_key_id,
            "managed_disk_cmk_key_vault_key_id": managed_disk_cmk_key_vault_key_id,
            "infrastructure_encryption_enabled": infrastructure_encryption_enabled,
            "security_profile_enabled": security_profile_enabled,
            
            # Monitoring Configuration
            "enhanced_monitoring_enabled": enhanced_monitoring_enabled,
            
            # Update Configuration
            "automatic_update": automatic_update,
            "restart_no_updates": restart_no_updates,
            "day_of_week": day_of_week,
            "frequency": frequency,
            "hours": hours,
            "minutes": minutes,
            
            # Tags
            "tags": tags if tags else {},
        }
        
        # Remove None values to allow terraform defaults
        tfvars = {k: v for k, v in tfvars.items() if v is not None}
        
        # Log the configuration being used
        update_status(
            f"Configuration prepared with the following features:\n" +
            f"• Network: {'Custom VNet' if enable_vnet else 'Default'}\n" +
            f"• Security: {'Enhanced' if security_profile_enabled else 'Standard'}\n" +
            f"• Monitoring: {'Enhanced' if enhanced_monitoring_enabled else 'Standard'}\n" +
            f"• Updates: {'Automatic' if automatic_update else 'Manual'}",
            "📝"
        )
        
        with open(tfvars_path, 'w') as f:
            json.dump(tfvars, f, indent=2)

        # Initialize Terraform
        current_step = 4
        current_phase = "Initializing Terraform"
        update_status("Initializing Terraform backend", "🔧")
        backend_config = [
            f"storage_account_name={storage_account_name}",
            f"container_name={container_name}",
            f"key=databricks/{workspace_name}/terraform.tfstate",
            f"resource_group_name={resource_group_name}",
            f"subscription_id={os.environ['ARM_SUBSCRIPTION_ID']}"
        ]
        run_command(["terraform", "init"] + [f"-backend-config={c}" for c in backend_config], cwd=tf_dir)

        # Generate and show plan
        current_step = 5
        current_phase = "Planning Changes"
        update_status("Generating Terraform plan", "📋")
        plan_output = run_command(
            ["terraform", "plan", "-var-file=terraform.tfvars.json"],
            cwd=tf_dir,
            capture_output=True
        )
        update_status("Reviewing planned changes", "📋")

        # Apply Terraform
        current_step = 6
        current_phase = "Applying Changes"
        update_status("Applying Terraform configuration", "🚀")
        run_command(
            ["terraform", "apply", "-auto-approve", "-var-file=terraform.tfvars.json"],
            cwd=tf_dir
        )

        # Get workspace URL
        current_step = 7
        current_phase = "Finalizing"
        workspace_url = f"https://{run_command(['terraform', 'output', '-raw', 'databricks_host'], cwd=tf_dir, capture_output=True).strip()}"
        
        # Final success message
        update_status(
            f"Workspace successfully created!\nWorkspace URL: {workspace_url}",
            "✅"
        )

        return workspace_url

    except Exception as e:
        print(f"\n❌ Error: {str(e)}", file=sys.stderr)
        if message_ts:
            templates = load_slack_templates()
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
                        "text": f"*Error:*\n```{str(e)}```"
                    }
                }
            ]
            try:
                slack.chat_update(channel=channel_id, ts=message_ts, blocks=blocks)
            except SlackApiError:
                pass  # Don't fail if we can't update Slack
        raise
    finally:
        # Cleanup
        import shutil
        shutil.rmtree(workspace_dir, ignore_errors=True)