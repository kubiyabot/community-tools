import logging
from typing import Dict, Any, List, Optional
from kubiya_sdk.tools import Tool, Arg
from kubiya_sdk.tools.models import FileSpec
from pydantic import Field
import json

logger = logging.getLogger(__name__)

class CompaniesTool(Tool):
    """Tool for managing HubSpot companies."""
    
    def __init__(self, **data):
        super().__init__(**data)
        self.secrets = (self.secrets or []) + ["HUBSPOT_ACCESS_TOKEN"]
        if not self.icon_url:
            self.icon_url = "https://www.hubspot.com/hubfs/HubSpot_Logos/HubSpot-Inversed-Favicon.png"
        
        # Set execution environment
        self.image = "python:3.12"
        self.content = self._generate_script_content()
        
        # Add required files
        self.with_files = [
            FileSpec(
                destination="/opt/scripts/companies_ops.py",
                content=self._get_operations_script()
            ),
            FileSpec(
                destination="/opt/scripts/hubspot_runner.py",
                content=self._get_runner_script()
            )
        ]
    
    def _generate_script_content(self) -> str:
        """Generate the entrypoint script content."""
        return """#!/bin/sh
set -e

echo "🔧 Setting up HubSpot operation environment..."

# Validate environment
if [ -z "$HUBSPOT_ACCESS_TOKEN" ]; then
    echo "❌ HUBSPOT_ACCESS_TOKEN environment variable is required"
    exit 1
fi

# Create and activate virtual environment
echo "📦 Creating virtual environment..."
python -m venv /tmp/venv
. /tmp/venv/bin/activate

echo "📦 Installing dependencies..."
pip install --no-cache-dir hubspot-api-client>=8.1.0

echo "🚀 Running HubSpot operation..."
python /opt/scripts/hubspot_runner.py
"""

    def _get_operations_script(self) -> str:
        """Get the operations script content."""
        # This would be the content of companies_ops.py
        return """import logging
from typing import Dict, Any, List, Optional
import hubspot
from hubspot.crm.companies import ApiException

logger = logging.getLogger(__name__)

class CompaniesOperations:
    def __init__(self, access_token: str):
        self.client = hubspot.Client.create(access_token=access_token)
    
    # ... [operations methods] ...
"""

    def _get_runner_script(self) -> str:
        """Get the runner script content."""
        return """import os
import sys
import json
from companies_ops import CompaniesOperations

def main():
    # Get operation parameters
    operation = os.environ.get('HUBSPOT_OPERATION')
    params = json.loads(os.environ.get('OPERATION_PARAMS', '{}'))
    
    # Initialize operations
    ops = CompaniesOperations(access_token=os.environ['HUBSPOT_ACCESS_TOKEN'])
    
    # Execute operation
    result = getattr(ops, operation)(**params)
    
    # Output result
    print(json.dumps(result))

if __name__ == '__main__':
    main()
"""

    def create_company(self, name: str, properties: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create a new company in HubSpot."""
        self.env = {
            "HUBSPOT_OPERATION": "create_company",
            "OPERATION_PARAMS": json.dumps({
                "name": name,
                "properties": properties or {}
            })
        }
        return self.run()
    
    def get_company(self, company_id: str) -> Dict[str, Any]:
        """Get company details by ID."""
        self.env = {
            "HUBSPOT_OPERATION": "get_company",
            "OPERATION_PARAMS": json.dumps({
                "company_id": company_id
            })
        }
        return self.run()
    
    def update_company(self, company_id: str, properties: Dict[str, Any]) -> Dict[str, Any]:
        """Update company properties."""
        self.env = {
            "HUBSPOT_OPERATION": "update_company",
            "OPERATION_PARAMS": json.dumps({
                "company_id": company_id,
                "properties": properties
            })
        }
        return self.run()
    
    def search_companies(self, query: str, properties: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Search for companies based on a query."""
        self.env = {
            "HUBSPOT_OPERATION": "search_companies",
            "OPERATION_PARAMS": json.dumps({
                "query": query,
                "properties": properties
            })
        }
        return self.run()
    
    def delete_company(self, company_id: str) -> None:
        """Delete a company by ID."""
        self.env = {
            "HUBSPOT_OPERATION": "delete_company",
            "OPERATION_PARAMS": json.dumps({
                "company_id": company_id
            })
        }
        return self.run()
    
    def get_contacts(self, company_id: str) -> List[Dict[str, Any]]:
        """Get all contacts associated with a company."""
        self.env = {
            "HUBSPOT_OPERATION": "get_contacts",
            "OPERATION_PARAMS": json.dumps({
                "company_id": company_id
            })
        }
        return self.run() 