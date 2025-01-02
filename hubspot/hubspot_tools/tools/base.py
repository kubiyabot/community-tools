from kubiya_sdk.tools import Tool, FileSpec, Arg
from typing import Dict, Any, List, Optional
from .common import COMMON_ENV, COMMON_FILES, COMMON_SECRETS

HUBSPOT_ICON_URL = "https://www.hubspot.com/hubfs/HubSpot_Logos/HubSpot-Inversed-Favicon.png"
HUBSPOT_DOCKER_IMAGE = "python:3.12"

class HubSpotBaseTool(Tool):
    """Base class for HubSpot tools."""
    
    def __init__(self, name: str, description: str, content: str, args: List[Arg], long_running: bool = False):
        """Initialize the HubSpot tool."""
        
        # Enhance the script content with common setup
        enhanced_content = f"""#!/bin/sh
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
{content}
"""
        
        super().__init__(
            name=name,
            description=description,
            icon_url=HUBSPOT_ICON_URL,
            type="docker",
            image=HUBSPOT_DOCKER_IMAGE,
            content=enhanced_content,
            args=args,
            env=COMMON_ENV,
            files=COMMON_FILES,
            secrets=COMMON_SECRETS,
            long_running=long_running
        ) 