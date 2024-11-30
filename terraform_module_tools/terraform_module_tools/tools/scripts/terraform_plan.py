#!/usr/bin/env python3
import os
import sys
import json
import subprocess
from typing import Optional

def print_progress(message: str, emoji: str) -> None:
    """Print progress messages with emoji."""
    print(f"\n{emoji} {message}", flush=True)
    sys.stdout.flush()

def main():
    if len(sys.argv) != 3:
        print("Usage: terraform_plan.py <module_url> <variables_json>", file=sys.stderr)
        sys.exit(1)

    module_url = sys.argv[1]
    variables = json.loads(sys.argv[2])
    
    try:
        # Initialize state manager
        state_manager = TerraformStateManager(os.environ["KUBIYA_USER_EMAIL"])
        req_id = state_manager.create_apply_request("plan", variables)
        
        print_progress(f"Created plan request: {req_id}", "🎯")
        
        # Clone repository
        workspace_dir = state_manager.get_workspace_dir(req_id)
        print_progress("Cloning repository...", "📦")
        
        clone_cmd = ["git", "clone"]
        if "GH_TOKEN" in os.environ:
            auth_url = module_url.replace(
                "https://github.com",
                f"https://{os.environ['GH_TOKEN']}@github.com"
            )
            clone_cmd.append(auth_url)
        else:
            clone_cmd.append(module_url)
            
        clone_cmd.append(str(workspace_dir))
        subprocess.run(clone_cmd, check=True)
        
        # Change to workspace directory
        os.chdir(workspace_dir)
        
        # Initialize Terraform
        print_progress("Initializing Terraform...", "⚙️")
        subprocess.run(["terraform", "init"], check=True)
        
        # Create variables file
        print_progress("Generating variables file...", "📝")
        with open("terraform.tfvars.json", "w") as f:
            json.dump(variables, f, indent=2)
        
        # Generate plan
        print_progress("Generating Terraform plan...", "🔍")
        plan_output = subprocess.run(
            ["terraform", "plan", "-no-color"],
            capture_output=True,
            text=True,
            check=True
        ).stdout
        
        # Store plan
        state_manager.store_plan_output(req_id, plan_output)
        
        print_progress(f"Plan generated successfully with ID: {req_id}", "✅")
        print("\nPlan Output:")
        print(plan_output)
        
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main() 