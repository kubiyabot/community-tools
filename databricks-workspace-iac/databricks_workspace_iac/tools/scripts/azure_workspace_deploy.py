import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Dict, Any

from databricks_workspace_iac.tools.scripts.common import print_progress, run_command, SlackNotifier

def create_tfvars(args: Dict[str, Any], tfvars_path: Path) -> None:
    """Create terraform.tfvars.json file from arguments"""
    tfvars = {
        "workspace_name": args["workspace_name"],
        "location": args["region"],
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

def main():
    # Set up workspace
    workspace_dir = Path(tempfile.mkdtemp())
    os.environ["WORKSPACE_NAME"] = sys.argv[1]  # First arg is workspace name
    os.environ["REGION"] = sys.argv[2]  # Second arg is region
    
    # Initialize Slack notifier
    slack = SlackNotifier()

    try:
        # Initial Slack message
        print_progress("Starting Databricks Workspace deployment...", "🚀")
        slack.send_initial_message("Initializing Databricks Workspace deployment...")
        slack.update_progress(
            "🚀 Deployment Started",
            "Preparing to create workspace...",
            "1"
        )

        # Clone repository
        print_progress("Cloning Infrastructure Repository...", "📦")
        repo_dir = workspace_dir / "repo"
        run_command([
            "git", "clone",
            f"https://{os.environ['PAT']}@github.com/{os.environ['GIT_ORG']}/{os.environ['GIT_REPO']}.git",
            str(repo_dir)
        ])
        slack.update_progress("📦 Repository Cloned", "Infrastructure repository cloned successfully", "1")

        # Create terraform.tfvars.json
        tf_dir = repo_dir / "aux/databricks/terraform/azure"
        tfvars_path = tf_dir / "terraform.tfvars.json"
        create_tfvars(dict(zip(sys.argv[1::2], sys.argv[2::2])), tfvars_path)

        # Initialize Terraform
        print_progress("Initializing Terraform...", "⚙️")
        backend_config = [
            f"storage_account_name={os.environ['STORAGE_ACCOUNT_NAME']}",
            f"container_name={os.environ['CONTAINER_NAME']}",
            f"key=databricks/{os.environ['WORKSPACE_NAME']}/terraform.tfstate",
            f"resource_group_name={os.environ['RESOURCE_GROUP_NAME']}",
            f"subscription_id={os.environ['ARM_SUBSCRIPTION_ID']}"
        ]
        
        run_command(["terraform", "init"] + [f"-backend-config={c}" for c in backend_config], cwd=tf_dir)
        slack.update_progress("⚙️ Terraform Initialized", "Terraform successfully initialized", "2")

        # Generate and show plan
        print_progress("Generating Terraform plan...", "📋")
        plan_output = run_command(
            ["terraform", "plan", "-var-file=terraform.tfvars.json"], 
            cwd=tf_dir, 
            capture_output=True
        )
        slack.update_progress(
            "📋 Terraform Plan Generated",
            "Reviewing changes to be made...",
            "2",
            plan_output=plan_output
        )

        # Apply Terraform
        print_progress("Applying Terraform configuration...", "🚀")
        def handle_terraform_output(line: str) -> None:
            print(line, flush=True)
            if "Creating..." in line:
                resource = line.split('"')[1]
                slack.update_progress(
                    "🚀 Deploying Resources",
                    f"Creating resource: {resource}",
                    "3"
                )
            elif "Apply complete!" in line:
                slack.update_progress(
                    "✅ Resources Deployed",
                    "All resources have been successfully created",
                    "4"
                )

        run_command(
            ["terraform", "apply", "-auto-approve", "-var-file=terraform.tfvars.json"],
            cwd=tf_dir,
            stream_output=True,
            callback=handle_terraform_output
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
            "✅ Deployment Successful",
            f"Databricks workspace *{os.environ['WORKSPACE_NAME']}* has been successfully provisioned!",
            "4",
            workspace_url=workspace_url
        )

    except Exception as e:
        print(f"\n❌ Error: {str(e)}", file=sys.stderr)
        slack.send_error(str(e))
        sys.exit(1)

    finally:
        # Cleanup
        import shutil
        shutil.rmtree(workspace_dir, ignore_errors=True)

if __name__ == "__main__":
    main() 