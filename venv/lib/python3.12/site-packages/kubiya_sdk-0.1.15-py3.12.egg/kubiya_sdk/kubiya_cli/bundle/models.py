from pydantic import BaseModel

from kubiya_sdk.tools.models import Tool


class DiscoveryError(BaseModel):
    file: str
    error: str
    error_type: str
    suggestion: str = ""


class BundleModel(BaseModel):
    tools: list[Tool]
    errors: list[DiscoveryError]
    python_bundle_version: str
