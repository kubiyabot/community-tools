from kubiya_sdk.tools import Tool
from typing import Optional, List, Dict, Any

DATABRICKS_ICON_URL = "https://www.databricks.com/wp-content/themes/databricks/assets/images/databricks-logo.svg"


class DatabricksApiTool(Tool):
    def __init__(
        self,
        **kwargs
    ):
        # Set default values
        kwargs.setdefault('args', [])
        kwargs.setdefault('env', [])
        kwargs.setdefault('secrets', [])
        kwargs.setdefault('long_running', False)
        kwargs.setdefault('with_files', None)
        kwargs.setdefault('image', "alpine:latest")
        
        # Add required Databricks-specific attributes
        kwargs['icon_url'] = DATABRICKS_ICON_URL
        kwargs['type'] = "docker"

        # Initialize the parent class with all kwargs
        super().__init__(**kwargs)
