from kubiya_sdk.tools import Tool
from typing import Optional, List, Dict, Any

DATABRICKS_ICON_URL = "https://www.databricks.com/wp-content/themes/databricks/assets/images/databricks-logo.svg"


class DatabricksApiTool(Tool):
    # Define class variables with type annotations
    name: str
    description: str
    content: str
    args: List[Any] = []
    env: List[Any] = []
    secrets: List[Any] = []
    long_running: bool = False
    with_files: Optional[Dict[str, Any]] = None
    image: str = "alpine:latest"
    mermaid: Optional[str] = None
    icon_url: str = DATABRICKS_ICON_URL
    type: str = "docker"

    # Remove the __init__ method to let Pydantic handle initialization
