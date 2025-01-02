"""Common configurations for HubSpot tools."""

from kubiya_sdk.tools import FileSpec

COMMON_ENV = []

runner_script = '''import os
import sys
import json
import logging
from typing import Dict, Any, List, Optional
import hubspot
from hubspot.crm import contacts, companies, deals
from hubspot.crm.associations import ApiException

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def execute_operation():
    """Execute the requested HubSpot operation."""
    try:
        # Load configuration
        with open('/tmp/hubspot_config.json', 'r') as f:
            config = json.load(f)
            
        # Execute operation
        result = config['operation'](**config['parameters'])
        
        # Return result
        if result is not None:
            print(json.dumps({"result": result}))
            
    except Exception as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(1)

if __name__ == '__main__':
    execute_operation()
'''

COMMON_FILES = [
    FileSpec(
        destination="/opt/scripts/hubspot_runner.py",
        content=runner_script
    )
]

COMMON_SECRETS = [
    "HUBSPOT_ACCESS_TOKEN"  # HubSpot API Token - https://developers.hubspot.com/docs/api/overview
] 