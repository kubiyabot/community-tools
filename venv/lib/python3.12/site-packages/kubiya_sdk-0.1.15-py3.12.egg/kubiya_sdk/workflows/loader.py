# kubiya_sdk/workflows/workflow_loader.py

import os
import importlib.util

from .stateful_workflow import StatefulWorkflow


def load_workflow_from_file(file_path):
    """
    Load a workflow from a Python file.
    The file should contain a 'create_workflow' function that returns a StatefulWorkflow instance.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Workflow file not found: {file_path}")

    spec = importlib.util.spec_from_file_location("workflow_module", file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    if not hasattr(module, "create_workflow"):
        raise AttributeError("The workflow file must contain a 'create_workflow' function")

    workflow = module.create_workflow()
    if not isinstance(workflow, StatefulWorkflow):
        raise TypeError("The 'create_workflow' function must return a StatefulWorkflow instance")

    return workflow
