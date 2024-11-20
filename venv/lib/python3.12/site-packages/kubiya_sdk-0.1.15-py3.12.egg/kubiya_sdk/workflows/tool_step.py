from typing import Any, Dict

from .step import WorkflowStep
from ..stream.manager import nats_manager
from ..tools.registry import tool_registry


class ToolStep(WorkflowStep):
    def __init__(
        self,
        name: str,
        tool_name: str,
        source_url: str,
        description: str = None,
        icon: str = None,
        label: str = None,
    ):
        super().__init__(name, lambda x: x, description, icon, label)
        self.tool_name = tool_name
        self.source_url = source_url

    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        tool = tool_registry.get_tool(self.source_url, self.tool_name)
        if tool is None:
            raise ValueError(f"Tool '{self.tool_name}' not found in registry for source '{self.source_url}'")

        # Validate inputs
        validated_inputs = tool.validate_inputs(state)

        if nats_manager.is_connected:
            # Execute via NATS
            result = await nats_manager.publish_request(
                "$org.tool-manager.execute",
                {
                    "source_url": self.source_url,
                    "tool_name": self.tool_name,
                    "inputs": validated_inputs,
                },
            )
        else:
            # Execute via HTTP
            result = await tool.execute(validated_inputs)

        return result

    def then(self, next_step: str):
        self.next_steps.append(next_step)
        return self

    def when(self, condition: str, then_step: str):
        self.conditions.append({"condition": condition, "then": then_step})
        return self

    def otherwise(self, else_step: str):
        self.conditions.append({"condition": "True", "then": else_step})
        return self

    def get_next_step(self, state: Dict[str, Any]) -> str:
        for condition in self.conditions:
            if eval(condition["condition"], {}, {"state": state}):
                return condition["then"]
        if self.next_steps:
            return self.next_steps[0]
        return "__end__"
