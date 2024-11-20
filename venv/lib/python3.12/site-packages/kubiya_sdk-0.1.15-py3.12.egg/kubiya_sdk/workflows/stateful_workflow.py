import asyncio
from typing import Any, Dict, List, Union, Callable, Optional, AsyncIterator

from pydantic import BaseModel

from .state import WorkflowState
from .tool_step import ToolStep
from ..tools.models import ServiceSpec
from ..utils.logger import SDKLogger

END = "__end__"


class WorkflowStep:
    def __init__(
        self,
        func: Callable,
        name: str,
        description: str = None,
        icon: str = None,
        label: str = None,
        input_schema: Dict[str, Any] = None,
    ):
        self.func = func
        self.name = name
        self.description = description
        self.icon = icon
        self.label = label
        self.next_steps: List[str] = []
        self.conditions: List[Dict[str, Any]] = []
        self.input_schema = input_schema

    async def execute(self, state: WorkflowState) -> Dict[str, Any]:
        if self.input_schema:
            state = self.validate_inputs(state)
        if asyncio.iscoroutinefunction(self.func):
            return await self.func(state)
        else:
            return self.func(state)

    def then(self, next_step: str):
        self.next_steps.append(next_step)
        return self

    def when(self, condition: str, then_step: str):
        self.conditions.append({"condition": condition, "then": then_step})
        return self

    def otherwise(self, else_step: str):
        self.conditions.append({"condition": "True", "then": else_step})
        return self

    def get_next_step(self, state: WorkflowState) -> str:
        for condition in self.conditions:
            if eval(condition["condition"], {"state": state}):
                return condition["then"]
        if self.next_steps:
            return self.next_steps[0]
        return END

    def validate_inputs(self, state: WorkflowState) -> WorkflowState:
        try:
            validated = BaseModel(**state.to_dict())
            return WorkflowState(validated.dict())
        except Exception as e:
            raise ValueError(f"Invalid inputs: {str(e)}")


class StatefulWorkflow:
    def __init__(self, name: str, description: str = "", services: List[ServiceSpec] = None):
        self.name = name
        self.description = description
        self.steps: Dict[str, WorkflowStep] = {}
        self.entry_point: Optional[str] = None
        self.logger = SDKLogger()
        self.state = WorkflowState()
        self.services: List[ServiceSpec] = services or []

    def add_step(
        self,
        name: str,
        func: Callable,
        description: str = None,
        icon: str = None,
        label: str = None,
    ):
        step = WorkflowStep(func, name, description, icon, label)
        self.steps[name] = step
        if not self.entry_point:
            self.entry_point = name
        return step

    def step(self, name: str, description: str = None, icon: str = None, label: str = None):
        def decorator(func):
            return self.add_step(name, func, description, icon, label)

        return decorator

    def add_edge(self, from_step: str, to_step: str):
        if from_step not in self.steps:
            raise ValueError(f"Step '{from_step}' not found in workflow")
        if to_step not in self.steps and to_step != END:
            raise ValueError(f"Step '{to_step}' not found in workflow")
        self.steps[from_step].then(to_step)

    def add_service(self, service: ServiceSpec):
        self.services.append(service)

    async def run(
        self,
        initial_state: Union[Dict[str, Any], BaseModel],
        env_vars: Dict[str, str] = None,
        files: Dict[str, str] = None,
    ) -> List[Dict[str, Any]]:
        if isinstance(initial_state, BaseModel):
            initial_state = initial_state.dict()

        if env_vars:
            import os

            os.environ.update(env_vars)

        if files:
            for file_name, content in files.items():
                with open(file_name, "w") as f:
                    f.write(content)

        return await self._run_async(initial_state)

    async def _run_async(self, initial_state: Dict[str, Any]) -> List[Dict[str, Any]]:
        return [step_result async for step_result in self._execute_steps(initial_state)]

    async def _execute_steps(self, initial_state: Dict[str, Any]) -> AsyncIterator[Dict[str, Any]]:
        self.state = WorkflowState(initial_state)
        current_step_name = self.entry_point

        while current_step_name != END:
            step = self.steps[current_step_name]
            self.logger.log(f"Executing step: {current_step_name}", step=current_step_name)

            try:
                result = await step.execute(self.state)
                self.state.update(result)
                yield {
                    "step": current_step_name,
                    "status": "completed",
                    "state": self.state.to_dict(),
                }
            except Exception as e:
                self.logger.log(
                    f"Error in step '{current_step_name}': {str(e)}",
                    step=current_step_name,
                    level="ERROR",
                )
                yield {
                    "step": current_step_name,
                    "status": "error",
                    "error": str(e),
                    "state": self.state.to_dict(),
                }
                raise

            current_step_name = step.get_next_step(self.state)

        self.logger.log("Workflow completed")
        yield {"step": END, "status": "completed", "state": self.state.to_dict()}

    def to_mermaid(self) -> str:
        mermaid = [
            "graph TD",
            "classDef defaultClass fill:#FFFFFF,stroke:#333,stroke-width:2px,font-family:'Arial',font-weight:bold;",
            "classDef startClass fill:#32CD32,stroke:#333,stroke-width:2px,font-family:'Arial',font-weight:bold;",
            "classDef endClass fill:#FF6347,stroke:#333,stroke-width:2px,font-family:'Arial',font-weight:bold;",
            "classDef conditionClass fill:#FFD700,stroke:#333,stroke-width:2px,font-family:'Arial',font-weight:bold;",
            "classDef actionClass fill:#ADD8E6,stroke:#333,stroke-width:2px,font-family:'Arial',font-weight:bold;",
            "classDef toolClass fill:#FF69B4,stroke:#333,stroke-width:2px,font-family:'Arial',font-weight:bold;",
            "classDef parallelClass fill:#9370DB,stroke:#333,stroke-width:2px,font-family:'Arial',font-weight:bold;",
        ]

        for step_name, step in self.steps.items():
            # Determine the class based on the step type or conditions
            if step.conditions:
                step_class = "conditionClass"
                label = f"🔀 {step.label or step.name}"
            elif step.name.lower().startswith("start"):
                step_class = "startClass"
                label = f"🚀 {step.label or step.name}"
            elif step.name.lower().startswith("end"):
                step_class = "endClass"
                label = f"🏁 {step.label or step.name}"
            elif isinstance(step, ToolStep):
                step_class = "toolClass"
                label = f"🛠️ {step.label or step.name}"
            elif "parallel" in step.name.lower():
                step_class = "parallelClass"
                label = f"🔗 {step.label or step.name}"
            else:
                step_class = "actionClass"
                label = f"⚙️ {step.label or step.name}"

            mermaid.append(f'{step_name}["{label}"]:::{step_class}')

            for next_step in step.next_steps:
                if next_step == END:
                    mermaid.append(f'{step_name} --> END["🏁 End"]:::endClass')
                else:
                    mermaid.append(f"{step_name} --> {next_step}")

            for condition in step.conditions:
                condition_text = condition["condition"].replace('"', "'")
                then_step = condition["then"]
                if then_step == END:
                    mermaid.append(f'{step_name} -->|"{condition_text} ✅"| END:::{step_class}')
                else:
                    mermaid.append(f'{step_name} -->|"{condition_text} ➡️"| {then_step}:::{step_class}')

        # Ensure the final step is always connected to the "End" node
        last_step_name = list(self.steps.keys())[-1]
        if "END" not in [step["then"] for step in self.steps[last_step_name].conditions] and last_step_name != "END":
            mermaid.append(f'{last_step_name} --> END["🏁 End"]:::endClass')

        # Add more visual styling to links and edges
        mermaid.append("linkStyle default stroke:#2d7dd2,stroke-width:2px,stroke-dasharray: 5,5;")

        return "\n".join(mermaid)

    @classmethod
    def from_dict(cls, workflow_dict: Dict[str, Any]):
        workflow = cls(workflow_dict["name"])
        workflow.description = workflow_dict.get("description", "")
        workflow.services = [ServiceSpec(**service) for service in workflow_dict.get("services", [])]
        for step_dict in workflow_dict["steps"]:
            workflow.add_step(
                step_dict["name"],
                lambda x: x,  # Placeholder function
                step_dict.get("description"),
                step_dict.get("icon"),
                step_dict.get("label"),
            )
        for step_dict in workflow_dict["steps"]:
            for next_step in step_dict.get("next_steps", []):
                workflow.add_edge(step_dict["name"], next_step)
            for condition in step_dict.get("conditions", []):
                workflow.add_condition(step_dict["name"], condition["condition"], condition["then"])
        return workflow

    def add_condition(self, step: str, condition: str, then_step: str):
        if step not in self.steps:
            raise ValueError(f"Step '{step}' not found in workflow")
        if then_step not in self.steps and then_step != END:
            if then_step == "END":
                then_step = END
            else:
                raise ValueError(f"Step '{then_step}' not found in workflow")
        self.steps[step].when(condition, then_step)

    def add_parallel_group(
        self,
        name: str,
        steps: List[str],
        description: str = None,
        icon: str = None,
        label: str = None,
    ):
        group_step = self.add_step(name, lambda x: x, description, icon, label)
        for step_name in steps:
            group_step.then(step_name)
        return group_step

    def add_tool_step(
        self,
        name: str,
        tool_name: str,
        source_url: str,
        description: str = None,
        icon: str = None,
        label: str = None,
    ):
        step = ToolStep(name, tool_name, source_url, description, icon, label)
        self.steps[name] = step
        if not self.entry_point:
            self.entry_point = name
        return step
