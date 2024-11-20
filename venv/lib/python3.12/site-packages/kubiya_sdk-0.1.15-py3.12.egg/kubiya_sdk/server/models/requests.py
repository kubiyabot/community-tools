from typing import Any, Dict, Optional

from pydantic import Field, BaseModel


class DiscoverRequest(BaseModel):
    source: str


class RunRequest(BaseModel):
    source: str
    name: str
    inputs: Dict[str, Any] = Field(default_factory=dict, description="Input data for the workflow or tool")
    env: Dict[str, str] = Field(default_factory=dict, description="Environment variables")
    files: Dict[str, str] = Field(
        default_factory=dict,
        description="File mappings (key: file name, value: file content or path)",
    )


class DescribeRequest(BaseModel):
    source: str
    name: str
    filter: Optional[str] = None


class VisualizeRequest(BaseModel):
    source: str
    workflow: str
    format: str = "mermaid"
