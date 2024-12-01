#!/usr/bin/env python3
import os
import sys
import json
import time
import subprocess
import re
import shutil
from pathlib import Path
from typing import Dict, Any, Optional

class WorkspaceManager:
    def __init__(self, user_email: str, module_name: str):
        self.user_email = user_email
        self.module_name = module_name
        self.base_dir = Path(f"/tmp/terraform_workspaces/{user_email}")
        self.module_dir = self.base_dir / module_name
        self.current_workspace = None

    def setup(self) -> Path:
        """Setup and return workspace directory"""
        self.base_dir.mkdir(parents=True, exist_ok=True)
        return self.base_dir

    def get_module_dir(self) -> Path:
        """Get the module directory"""
        return self.module_dir

    def create_workspace(self) -> Path:
        """Create a new workspace for this operation"""
        timestamp = int(time.time())
        self.current_workspace = self.base_dir / f"{self.module_name}_run_{timestamp}"
        self.current_workspace.mkdir(parents=True, exist_ok=True)
        return self.current_workspace

def print_progress(message: str, emoji: str) -> None:
    """Print progress messages with emoji."""
    print(f"\n{emoji} {message}", flush=True)
    sys.stdout.flush()

def handle_repository(source_config: Dict[str, Any], workspace: WorkspaceManager) -> None:
    """Handle repository setup based on source configuration"""
    module_dir = workspace.get_module_dir()
    source_type = source_config.get('type', 'git')
    location = source_config['location']

    if source_type == 'git':
        git_config = source_config.get('git_config', {})
        
        if module_dir.exists():
            print_progress("Repository exists, updating...", "🔄")
            # Reset any local changes
            subprocess.run(["git", "reset", "--hard"], cwd=module_dir, check=True)
            subprocess.run(["git", "clean", "-fdx"], cwd=module_dir, check=True)
            # Fetch latest
            subprocess.run(["git", "fetch", "--all"], cwd=module_dir, check=True)
            # Checkout specific branch/tag or main
            ref = git_config.get('tag') or git_config.get('branch', 'main')
            subprocess.run(["git", "checkout", ref], cwd=module_dir, check=True)
            subprocess.run(["git", "pull"], cwd=module_dir, check=True)
        else:
            print_progress("Cloning repository...", "📦")
            clone_cmd = ["git", "clone"]
            if "GH_TOKEN" in os.environ:
                auth_url = location.replace(
                    "https://github.com",
                    f"https://{os.environ['GH_TOKEN']}@github.com"
                )
                clone_cmd.append(auth_url)
            else:
                clone_cmd.append(location)
            
            clone_cmd.append(str(module_dir))
            subprocess.run(clone_cmd, check=True)
            
            # Checkout specific branch/tag if specified
            if git_config.get('tag'):
                subprocess.run(["git", "checkout", git_config['tag']], cwd=module_dir, check=True)
            elif git_config.get('branch'):
                subprocess.run(["git", "checkout", git_config['branch']], cwd=module_dir, check=True)

    elif source_type == 'local':
        print_progress("Copying local files...", "📂")
        if module_dir.exists():
            shutil.rmtree(module_dir)
        shutil.copytree(location, module_dir)

    # Handle subfolder if specified
    if source_type == 'git' and source_config.get('git_config', {}).get('subfolder'):
        return module_dir / source_config['git_config']['subfolder']
    
    return module_dir

def run_pre_script(script_content: str, work_dir: Path) -> None:
    """Run pre-script if provided"""
    if not script_content:
        return

    print_progress("Running pre-script...", "🔧")
    script_path = work_dir / "pre_script.sh"
    
    # Write script to file
    with open(script_path, 'w') as f:
        f.write(script_content)
    
    # Make executable
    script_path.chmod(0o755)
    
    # Run script
    try:
        subprocess.run([str(script_path)], cwd=work_dir, check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Pre-script failed: {str(e)}", file=sys.stderr)
        raise

def handle_terraform_output(line: str) -> None:
    """Process and display Terraform output with nice formatting"""
    if "Creating..." in line:
        print(f"🔨 {line}", flush=True)
    elif "Modifying..." in line:
        print(f"📝 {line}", flush=True)
    elif "Destroying..." in line:
        print(f"🗑️ {line}", flush=True)
    elif "Error:" in line:
        print(f"❌ {line}", flush=True)
    elif "Apply complete!" in line:
        print(f"✅ {line}", flush=True)
    else:
        print(line, flush=True)

def main():
    if len(sys.argv) != 2:
        print("Usage: terraform_apply.py <source_config_json>", file=sys.stderr)
        sys.exit(1)

    source_config = json.loads(sys.argv[1])
    variables = json.loads(os.environ.get("variables", "{}"))
    user_email = os.environ.get("KUBIYA_USER_EMAIL", "default")
    module_name = source_config['location'].split("/")[-1].replace(".git", "")

    try:
        # Initialize workspace manager
        workspace = WorkspaceManager(user_email, module_name)
        workspace.setup()

        # Handle repository setup
        work_dir = handle_repository(source_config, workspace)
        
        # Run pre-script if provided
        if "pre_script" in source_config:
            run_pre_script(source_config["pre_script"], work_dir)

        # Create new workspace for this run
        run_workspace = workspace.create_workspace()
        
        # Copy module files to run workspace
        shutil.copytree(str(work_dir), str(run_workspace), dirs_exist_ok=True)
        
        # Change to run workspace
        os.chdir(run_workspace)

        # Initialize Terraform
        print_progress("Initializing Terraform...", "⚙️")
        subprocess.run(["terraform", "init"], check=True)

        # Create variables file
        print_progress("Setting up variables...", "📝")
        with open("terraform.tfvars.json", "w") as f:
            json.dump(variables, f, indent=2)

        # Apply changes
        print_progress("Applying changes...", "🚀")
        process = subprocess.Popen(
            ["terraform", "apply", "-auto-approve"],
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
                handle_terraform_output(line.rstrip())

        if process.returncode != 0:
            raise subprocess.CalledProcessError(process.returncode, "terraform apply")

        print_progress("Infrastructure successfully created!", "✨")

    except Exception as e:
        print(f"\n❌ Error: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main() 