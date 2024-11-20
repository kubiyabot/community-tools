import logging
from typing import Any, Dict, List

import requests
from pydantic import ValidationError

from .models import Tool, ToolOutput  # Updated import

logger = logging.getLogger(__name__)


class ToolManagerBridge:
    def __init__(self, base_url: str):
        self.base_url = base_url

    def get_tool_names(self) -> List[str]:
        logger.info(f"Getting tools from {self.base_url}")
        req = requests.get(f"{self.base_url}/tools")
        try:
            req.raise_for_status()
        except requests.HTTPError as e:
            raise Exception(f"Error getting tools: {req.text}") from e

        return req.json()

    def get_tool(self, tool_name: str) -> Tool:
        logger.info(f"Getting tool {tool_name} from {self.base_url}")
        req = requests.get(f"{self.base_url}/tools/{tool_name}")
        try:
            req.raise_for_status()
        except requests.HTTPError as e:
            raise Exception(f"Error getting tool {tool_name}: {req.text}") from e

        return Tool(**req.json())

    def execute(
        self,
        tool_name: str,
        args: Dict[str, Any],
    ) -> ToolOutput:
        logger.info(f"Executing tool {tool_name} with args: {args}")
        res = requests.post(
            f"{self.base_url}/execute",
            json={
                "args": args,
                "async": False,
                "files": {},  # You can handle files here based on your implementation
                "env_vars": {},  # You can handle environment variables here based on your implementation
                "tool_name": tool_name,
            },
        )
        logger.info(f"Tool {tool_name} executed, response: {res}")
        try:
            res.raise_for_status()
        except requests.HTTPError as e:
            raise Exception(f"Error executing tool {tool_name}: {res.text}") from e

        logger.info(f"Tool {tool_name} executed")
        try:
            return ToolOutput(**res.json())
        except ValidationError:
            raise Exception(f"Error parsing tool output: {res.text}")
