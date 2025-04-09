import logging
from typing import Dict, Any, List, Optional
from kubiya_sdk.tools import Tool, Arg
from kubiya_sdk.tools.models import FileSpec
from pydantic import Field
from pathlib import Path
import json

logger = logging.getLogger(__name__)

class HubspotTool(Tool):
    """Tool for executing HubSpot operations."""
    
    operation: str = Field(description="The HubSpot operation to execute")
    entity_type: str = Field(description="The type of entity to operate on (contacts, companies, deals, etc)")
    parameters: Dict[str, Any] = Field(default={}, description="Operation parameters")
    page_size: int = Field(default=100, description="Number of results per page for search operations")
    max_results: int = Field(default=1000, description="Maximum number of results to return for search operations")
    
    def __init__(self, **data):
        """Initialize the HubSpot tool."""
        super().__init__(**data)
        
        # Add required secrets
        self.secrets = (self.secrets or []) + ["HUBSPOT_ACCESS_TOKEN"]
        
        # Set default icon
        if not self.icon_url:
            self.icon_url = "https://www.hubspot.com/hubfs/HubSpot_Logos/HubSpot-Inversed-Favicon.png"
            
        # Generate mermaid diagram for operation flow
        self.mermaid = self._generate_mermaid_diagram()
        
    def _generate_mermaid_diagram(self) -> str:
        """Generate a mermaid diagram showing the operation flow."""
        return """
        sequenceDiagram
            participant U as User
            participant K as Kubiya
            participant H as HubSpot
            
            U->>K: Request operation
            K->>H: Execute operation
            
            alt Search Operation
                loop Pagination
                    K->>H: Fetch page
                    H-->>K: Page results
                end
            else Single Operation
                H-->>K: Operation result
            end
            
            K-->>U: Final result
        """

    def _generate_script_content(self) -> str:
        """Generate the script content for operation execution."""
        return """#!/bin/sh
set -e

echo "🔧 Setting up HubSpot operation environment..."

# Validate environment
if [ -z "$HUBSPOT_ACCESS_TOKEN" ]; then
    echo "❌ HUBSPOT_ACCESS_TOKEN environment variable is required"
    exit 1
fi

echo "📦 Installing dependencies..."
pip install -q hubspot-api-client>=8.1.0

echo "🚀 Running HubSpot operation..."
python3 /opt/scripts/hubspot_runner.py
"""

    def prepare(self) -> None:
        """Prepare the tool for execution."""
        try:
            logger.debug(f"Preparing tool for {self.operation} operation on {self.entity_type}")
            
            # Set up script content
            self.content = self._generate_script_content()
            
            # Set Python image
            self.image = "python:3.12"
            
            # Read the runner script
            script_path = Path(__file__).parent.parent / 'scripts' / 'hubspot_runner.py'
            with open(script_path, 'r') as file:
                hubspot_runner_script = file.read()
            
            # Add required files
            self.with_files = [
                FileSpec(
                    destination="/opt/scripts/hubspot_runner.py",
                    content=hubspot_runner_script
                ),
                FileSpec(
                    destination="/tmp/hubspot_config.json",
                    content=json.dumps({
                        'entity_type': self.entity_type,
                        'operation': self.operation,
                        'parameters': self.parameters,
                        'page_size': self.page_size,
                        'max_results': self.max_results
                    })
                )
            ]
            
            logger.debug("Tool preparation completed successfully")
            
        except Exception as e:
            logger.error(f"Failed to prepare tool: {str(e)}")
            raise

    def run_operation(self) -> Any:
        """Execute the HubSpot operation."""
        try:
            # Prepare the tool
            self.prepare()
            
            # Execute the operation
            result = self.run()
            
            # Parse the JSON result
            if isinstance(result, str):
                result_dict = json.loads(result)
                if "error" in result_dict:
                    raise Exception(result_dict["error"])
                return result_dict.get("result")
            return result
            
        except Exception as e:
            logger.error(f"Operation execution failed: {str(e)}")
            raise 