import os
import json
from datetime import datetime
import pytz

# Add error handling for imports
try:
    from zoomus import ZoomClient
except ImportError:
    print("### ⚠️ Note: This is likely a discovery call without the tool environment")
    print("Required package 'zoomus' will be installed during actual tool execution")
    # Create a dummy client for discovery
    class ZoomClient:
        def __init__(self, *args, **kwargs):
            pass

try:
    from .zoom_formatters import *
except ImportError:
    print("### ⚠️ Note: Running outside tool environment, formatters will be available during execution")

def get_zoom_client():
    """Initialize and return Zoom client with error handling"""
    try:
        return ZoomClient(os.environ['ZOOM_API_KEY'], os.environ['ZOOM_API_SECRET'])
    except Exception as e:
        print(f"❌ Failed to initialize Zoom client: {str(e)}")
        exit(1)

def handle_zoom_response(response, success_message="Operation completed successfully"):
    """Handle Zoom API response with proper error handling"""
    try:
        data = json.loads(response.content)
        if response.status_code in [200, 201, 204]:
            print(f"### ✅ {success_message}")
            return data
        else:
            error_msg = data.get('message', 'Unknown error')
            print("### ❌ Operation Failed")
            print(f"**Error**: {error_msg}")
            print(f"**Status Code**: {response.status_code}")
            exit(1)
    except Exception as e:
        print("### ❌ Error Processing Response")
        print(f"**Details**: {str(e)}")
        exit(1)

def validate_date(date_str, date_format="%Y-%m-%d"):
    """Validate date string format"""
    try:
        return datetime.strptime(date_str, date_format)
    except ValueError:
        print("### ❌ Invalid Date Format")
        print(f"Provided: `{date_str}`")
        print(f"Expected: `YYYY-MM-DD`")
        exit(1) 