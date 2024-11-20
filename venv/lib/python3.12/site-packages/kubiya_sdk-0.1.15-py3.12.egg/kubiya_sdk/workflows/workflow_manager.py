import os
from typing import Dict, List, Optional

import yaml

from .stateful_workflow import StatefulWorkflow


class WorkflowManager:
    def __init__(self):
        self.workflows: Dict[str, StatefulWorkflow] = {}

    def add_workflow(self, workflow: StatefulWorkflow):
        self.workflows[workflow.name] = workflow

    def get_workflow(self, name: str) -> Optional[StatefulWorkflow]:
        return self.workflows.get(name)

    def list_workflows(self) -> List[str]:
        return list(self.workflows.keys())

    def save_workflows(self, file_path: str = ".kubiya/workflows.yaml"):
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        workflow_data = {
            name: {
                "description": workflow.description,
                "steps": {
                    step_name: {
                        "description": step.description,
                        "icon": step.icon,
                        "label": step.label,
                        "next_steps": step.next_steps,
                        "conditions": step.conditions,
                    }
                    for step_name, step in workflow.steps.items()
                },
                "entry_point": workflow.entry_point,
            }
            for name, workflow in self.workflows.items()
        }
        with open(file_path, "w") as f:
            yaml.dump(workflow_data, f)

    @classmethod
    def load_workflows(cls, file_path: str = ".kubiya/workflows.yaml") -> "WorkflowManager":
        manager = cls()
        if os.path.exists(file_path):
            with open(file_path, "r") as f:
                workflow_data = yaml.safe_load(f)
            for name, data in workflow_data.items():
                workflow = StatefulWorkflow(name, data["description"])
                for step_name, step_data in data["steps"].items():
                    step = workflow.add_step(
                        step_name,
                        lambda state: state,  # Placeholder function
                        description=step_data["description"],
                        icon=step_data["icon"],
                        label=step_data["label"],
                    )
                    step.next_steps = step_data["next_steps"]
                    step.conditions = step_data["conditions"]
                workflow.entry_point = data["entry_point"]
                manager.add_workflow(workflow)
        return manager
