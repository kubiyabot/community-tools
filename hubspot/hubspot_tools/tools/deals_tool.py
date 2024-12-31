import logging
from typing import Dict, Any, List, Optional
from kubiya_sdk.tools import Tool, Arg
from kubiya_sdk.tools.models import FileSpec
from pydantic import Field
import json

logger = logging.getLogger(__name__)

class DealsTool(Tool):
    """Tool for managing HubSpot deals."""
    
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
                destination="/opt/scripts/deals_ops.py",
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
        # This would be the content of deals_ops.py
        return """import logging
from typing import Dict, Any, List, Optional
import hubspot
from hubspot.crm.deals import ApiException

logger = logging.getLogger(__name__)

class DealsOperations:
    def __init__(self, access_token: str):
        self.client = hubspot.Client.create(access_token=access_token)
    
    # ... [operations methods] ...
"""

    def _get_runner_script(self) -> str:
        """Get the runner script content."""
        return """import os
import sys
import json
from deals_ops import DealsOperations

def main():
    # Get operation parameters
    operation = os.environ.get('HUBSPOT_OPERATION')
    params = json.loads(os.environ.get('OPERATION_PARAMS', '{}'))
    
    # Initialize operations
    ops = DealsOperations(access_token=os.environ['HUBSPOT_ACCESS_TOKEN'])
    
    # Execute operation
    result = getattr(ops, operation)(**params)
    
    # Output result
    print(json.dumps(result))

if __name__ == '__main__':
    main()
"""

    def create_deal(self, deal_name: str, pipeline: str, stage: str, amount: Optional[float] = None, 
                   properties: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create a new deal in HubSpot."""
        self.env = {
            "HUBSPOT_OPERATION": "create_deal",
            "OPERATION_PARAMS": json.dumps({
                "deal_name": deal_name,
                "pipeline": pipeline,
                "stage": stage,
                "amount": amount,
                "properties": properties or {}
            })
        }
        return self.run()
    
    def get_deal(self, deal_id: str) -> Dict[str, Any]:
        """Get deal details by ID."""
        self.env = {
            "HUBSPOT_OPERATION": "get_deal",
            "OPERATION_PARAMS": json.dumps({
                "deal_id": deal_id
            })
        }
        return self.run()
    
    def update_deal(self, deal_id: str, properties: Dict[str, Any]) -> Dict[str, Any]:
        """Update deal properties."""
        self.env = {
            "HUBSPOT_OPERATION": "update_deal",
            "OPERATION_PARAMS": json.dumps({
                "deal_id": deal_id,
                "properties": properties
            })
        }
        return self.run()
    
    def search_deals(self, query: str, properties: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Search for deals based on a query."""
        self.env = {
            "HUBSPOT_OPERATION": "search_deals",
            "OPERATION_PARAMS": json.dumps({
                "query": query,
                "properties": properties
            })
        }
        return self.run()
    
    def delete_deal(self, deal_id: str) -> None:
        """Delete a deal by ID."""
        self.env = {
            "HUBSPOT_OPERATION": "delete_deal",
            "OPERATION_PARAMS": json.dumps({
                "deal_id": deal_id
            })
        }
        return self.run()
    
    def associate_with_company(self, deal_id: str, company_id: str) -> Dict[str, Any]:
        """Associate a deal with a company."""
        self.env = {
            "HUBSPOT_OPERATION": "associate_with_company",
            "OPERATION_PARAMS": json.dumps({
                "deal_id": deal_id,
                "company_id": company_id
            })
        }
        return self.run()
    
    def associate_with_contact(self, deal_id: str, contact_id: str) -> Dict[str, Any]:
        """Associate a deal with a contact."""
        self.env = {
            "HUBSPOT_OPERATION": "associate_with_contact",
            "OPERATION_PARAMS": json.dumps({
                "deal_id": deal_id,
                "contact_id": contact_id
            })
        }
        return self.run() 