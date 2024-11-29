from kubiya_sdk.tools import Tool, Arg, FileSpec
from typing import List, Optional
import os

class TerraformBaseTool(Tool):
    def __init__(
        self,
        name: str,
        description: str,
        terraform_module: str,
        script_name: str,
        args: List[Arg] = None,
        env: List[str] = None,
        secrets: List[str] = None,
    ):
        script_path = os.path.join(os.path.dirname(__file__), "scripts", script_name)
        
        super().__init__(
            name=name,
            description=description,
            type="docker",
            image="hashicorp/terraform:latest",
            content=f"python3 {script_path} {terraform_module}",
            args=args or [],
            env=env or [],
            secrets=secrets or [],
            with_files=[
                FileSpec(
                    source=script_path,
                    destination=f"/usr/local/bin/{script_name}"
                )
            ]
        )

class TerraformGetVarsTool(TerraformBaseTool):
    def __init__(self, **kwargs):
        description = """
        📋 Get Variables for Terraform Module
        
        Shows all available variables with their descriptions, types, and default values.
        Use this to understand what variables you need before planning or applying.
        """
        super().__init__(
            script_name="get_module_vars.py",
            description=description,
            **kwargs
        )

class TerraformPlanTool(TerraformBaseTool):
    def __init__(self, **kwargs):
        description = """
        🔍 Generate Terraform Plan
        
        Shows what changes would be made without applying them.
        Displays additions, modifications, and deletions in a clear format.
        """
        super().__init__(
            script_name="terraform_plan.py",
            description=description,
            args=[
                Arg(
                    name="variables",
                    description="JSON string of variables (e.g., '{\"vpc_name\": \"main\"}')",
                    required=True
                )
            ],
            **kwargs
        )

class TerraformApplyTool(TerraformBaseTool):
    def __init__(self, **kwargs):
        description = """
        🚀 Apply Terraform Configuration
        
        Applies the infrastructure changes with real-time progress updates.
        Shows detailed status of resource creation/modification/deletion.
        """
        super().__init__(
            script_name="terraform_apply.py",
            description=description,
            args=[
                Arg(
                    name="variables",
                    description="JSON string of variables (e.g., '{\"vpc_name\": \"main\"}')",
                    required=True
                )
            ],
            **kwargs
        )