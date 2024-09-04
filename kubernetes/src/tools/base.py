from kubiya_sdk.tools.models import Tool, Arg
from ..utils.script_runner import run_script
from ..config import config, get_kubectl_auth_args
import os

class BaseKubernetesTool(Tool):
    def __init__(self, name: str, description: str, script_template: str, args: list):
        super().__init__(
            name=name,
            type="python",
            description=description,
            args=args
        )
        self.script_template = script_template

    async def execute(self, args: dict) -> dict:
        script_path = os.path.join(os.path.dirname(__file__), '..', 'templates', self.script_template)
        with open(script_path, 'r') as f:
            script_content = f.read()

        # Add common variables and functions to the script
        script_content = f"""
#!/bin/bash
set -euo pipefail

KUBECTL_AUTH_ARGS="{get_kubectl_auth_args()}"
NAMESPACE="{args.get('namespace', config.namespace)}"

{script_content}
"""
        
        result = run_script(script_content, env_vars=args)
        return {"output": result}
