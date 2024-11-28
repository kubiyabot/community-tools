import os
import json
import subprocess
import tempfile
from typing import List, Dict, Any
from kubiya_sdk.tools import Tool, Arg

class TerraformModuleTool(Tool):
    def __init__(
        self,
        name: str,
        description: str,
        terraform_module: str,
        args: List[Arg] = None,
        env: List[str] = [],
        secrets: List[str] = [],
        with_files: Any = None,
        image: str = "hashicorp/terraform:latest",
        mermaid: str = None,
        auto_detect_vars: bool = True
    ):
        # If auto_detect_vars is True and no args provided, detect them from the module
        if auto_detect_vars and not args:
            args = self.detect_terraform_variables(terraform_module)
            
        # Generate the script content to apply the Terraform module
        content = self.generate_script(terraform_module, args or [])

        # Add GH_TOKEN to secrets if not present
        if "GH_TOKEN" not in secrets:
            secrets.append("GH_TOKEN")

        super().__init__(
            name=name,
            description=description,
            type="docker",
            image=image,
            content=content,
            args=args or [],
            env=env,
            secrets=secrets,
            with_files=with_files,
            mermaid=mermaid,
        )

    def detect_terraform_variables(self, module_url: str) -> List[Arg]:
        """
        Detect variables from a Terraform module by cloning it and parsing variables.tf
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                # Clone repository with token if available
                clone_cmd = ["git", "clone"]
                
                # Handle private repositories
                if "GH_TOKEN" in os.environ:
                    auth_url = module_url.replace(
                        "https://github.com",
                        f"https://{os.environ['GH_TOKEN']}@github.com"
                    )
                    clone_cmd.append(auth_url)
                else:
                    clone_cmd.append(module_url)
                    
                clone_cmd.append(temp_dir)
                
                subprocess.run(clone_cmd, check=True, capture_output=True)

                # Use terraform-config-inspect or parse variables.tf files
                variables = []
                
                # Try to find all variable definition files
                var_files = []
                for root, _, files in os.walk(temp_dir):
                    for file in files:
                        if file.endswith('.tf'):
                            with open(os.path.join(root, file), 'r') as f:
                                content = f.read()
                                if 'variable' in content:
                                    var_files.append(os.path.join(root, file))

                # Parse variable definitions using terraform show
                for var_file in var_files:
                    try:
                        # Initialize terraform in the directory
                        subprocess.run(
                            ["terraform", "init"],
                            cwd=os.path.dirname(var_file),
                            capture_output=True,
                            check=True
                        )
                        
                        # Use terraform show -json to get variable information
                        result = subprocess.run(
                            ["terraform", "show", "-json"],
                            cwd=os.path.dirname(var_file),
                            capture_output=True,
                            check=True,
                            text=True
                        )
                        
                        tf_data = json.loads(result.stdout)
                        
                        # Extract variables from the JSON output
                        if 'variables' in tf_data:
                            for var_name, var_data in tf_data['variables'].items():
                                variables.append(Arg(
                                    name=var_name,
                                    description=var_data.get('description', f"Variable {var_name}"),
                                    required=not var_data.get('default'),
                                    default=var_data.get('default')
                                ))
                    except subprocess.CalledProcessError:
                        # If terraform show fails, try parsing the file directly
                        with open(var_file, 'r') as f:
                            content = f.read()
                            # Basic regex parsing for variables
                            import re
                            var_blocks = re.finditer(
                                r'variable\s+"([^"]+)"\s*{([^}]+)}',
                                content,
                                re.MULTILINE | re.DOTALL
                            )
                            
                            for var_block in var_blocks:
                                var_name = var_block.group(1)
                                var_content = var_block.group(2)
                                
                                description = re.search(
                                    r'description\s*=\s*"([^"]+)"',
                                    var_content
                                )
                                default = re.search(
                                    r'default\s*=\s*([^\n]+)',
                                    var_content
                                )
                                
                                variables.append(Arg(
                                    name=var_name,
                                    description=description.group(1) if description else f"Variable {var_name}",
                                    required=not default,
                                    default=default.group(1) if default else None
                                ))

                return variables

            except Exception as e:
                print(f"Warning: Failed to detect variables automatically: {str(e)}")
                return []

    def generate_script(self, terraform_module: str, args: List[Arg]) -> str:
        script_lines = [
            "#!/bin/bash",
            "set -euo pipefail",
            "",
            "# Setup git credentials if GH_TOKEN is available",
            'if [ -n "${GH_TOKEN:-}" ]; then',
            '    git config --global url."https://${GH_TOKEN}@github.com/".insteadOf "https://github.com/"',
            'fi',
            "",
            "# Clone the Terraform module",
            f"git clone {terraform_module} /tmp/terraform_module",
            "",
            "cd /tmp/terraform_module",
            "",
            "# Initialize Terraform",
            "terraform init",
            "",
            "# Generate terraform.tfvars file",
            "cat <<EOF > terraform.tfvars",
        ]

        for arg in args:
            script_lines.append(f"{arg.name} = \"${{{arg.name}}}\"")
        
        script_lines.extend([
            "EOF",
            "",
            "# Show the plan",
            "terraform plan",
            "",
            "# Apply Terraform configuration",
            "terraform apply -auto-approve",
            ""
        ])

        return "\n".join(script_lines) 