from kubiya_sdk.tools.models import Tool

class InstEnvTool(Tool):
    """Base class for InstEnv API tools."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs) 