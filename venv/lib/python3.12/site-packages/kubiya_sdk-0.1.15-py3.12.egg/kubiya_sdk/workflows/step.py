import asyncio
from typing import Any, Dict, List, Callable

END = "__end__"


class WorkflowStep:
    def __init__(
        self,
        func: Callable,
        name: str,
        description: str = None,
        icon: str = None,
        label: str = None,
    ):
        self.func = func
        self.name = name
        self.description = description
        self.icon = icon
        self.label = label
        self.next_steps: List[str] = []
        self.conditions: List[Dict[str, Any]] = []

    def then(self, next_step: str):
        self.next_steps.append(next_step)
        return self

    def when(self, condition: str, then_step: str):
        self.conditions.append({"condition": condition, "then": then_step})
        return self

    def otherwise(self, else_step: str):
        self.conditions.append({"condition": "True", "then": else_step})
        return self

    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        if asyncio.iscoroutinefunction(self.func):
            result = await self.func(state)
        else:
            result = self.func(state)
        return {**state, **result}  # Merge the result with the existing state

    def get_next_step(self, state: Dict[str, Any]) -> str:
        for condition in self.conditions:
            if eval(condition["condition"], {}, {"state": state}):
                return condition["then"]
        return self.next_steps[0] if self.next_steps else END
