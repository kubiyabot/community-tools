import logging
from typing import Dict, Any, List, Optional
from kubiya_sdk.tools import Tool, Arg
from kubiya_sdk.tools.models import FileSpec
from pydantic import Field
import json

logger = logging.getLogger(__name__)

class ContactsTool(Tool):
    """Tool for managing HubSpot contacts."""
    
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
                destination="/opt/scripts/contacts_ops.py",
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

# Validate environment
if [ -z "$HUBSPOT_ACCESS_TOKEN" ]; then
    echo "❌ HUBSPOT_ACCESS_TOKEN environment variable is required"
    exit 1
fi

# Install dependencies
pip install -q hubspot-api-client>=8.1.0

# Run operation
python3 /opt/scripts/hubspot_runner.py
"""

    def _get_operations_script(self) -> str:
        """Get the operations script content."""
        # This would be the content of contacts_ops.py
        return """import logging
from typing import Dict, Any, List, Optional
import hubspot
from hubspot.crm.contacts import ApiException

logger = logging.getLogger(__name__)

class ContactsOperations:
    def __init__(self, access_token: str):
        self.client = hubspot.Client.create(access_token=access_token)
    
    # ... [operations methods] ...
"""

    def _get_runner_script(self) -> str:
        """Get the runner script content."""
        return """import os
import sys
import json
from contacts_ops import ContactsOperations

def main():
    # Get operation parameters
    operation = os.environ.get('HUBSPOT_OPERATION')
    params = json.loads(os.environ.get('OPERATION_PARAMS', '{}'))
    
    # Initialize operations
    ops = ContactsOperations(access_token=os.environ['HUBSPOT_ACCESS_TOKEN'])
    
    # Execute operation
    result = getattr(ops, operation)(**params)
    
    # Output result
    print(json.dumps(result))

if __name__ == '__main__':
    main()
"""

    def create_contact(self, email: str, firstname: str, lastname: str, properties: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create a new contact in HubSpot."""
        self.env = {
            "HUBSPOT_OPERATION": "create_contact",
            "OPERATION_PARAMS": json.dumps({
                "email": email,
                "firstname": firstname,
                "lastname": lastname,
                "properties": properties or {}
            })
        }
        return self.run()
    
    def get_contact(self, contact_id: str) -> Dict[str, Any]:
        """Get contact details by ID."""
        self.env = {
            "HUBSPOT_OPERATION": "get_contact",
            "OPERATION_PARAMS": json.dumps({
                "contact_id": contact_id
            })
        }
        return self.run()
    
    def update_contact(self, contact_id: str, properties: Dict[str, Any]) -> Dict[str, Any]:
        """Update contact properties."""
        self.env = {
            "HUBSPOT_OPERATION": "update_contact",
            "OPERATION_PARAMS": json.dumps({
                "contact_id": contact_id,
                "properties": properties
            })
        }
        return self.run()
    
    def search_contacts(self, query: str, properties: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Search for contacts based on a query."""
        self.env = {
            "HUBSPOT_OPERATION": "search_contacts",
            "OPERATION_PARAMS": json.dumps({
                "query": query,
                "properties": properties
            })
        }
        return self.run()
    
    def delete_contact(self, contact_id: str) -> None:
        """Delete a contact by ID."""
        self.env = {
            "HUBSPOT_OPERATION": "delete_contact",
            "OPERATION_PARAMS": json.dumps({
                "contact_id": contact_id
            })
        }
        return self.run() 