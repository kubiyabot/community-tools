import os
import sys
import logging
import importlib.util
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class WorkflowProjectLoader:
    def __init__(self, project_path: str):
        self.project_path = os.path.abspath(project_path)
        self.workflows: Dict[str, Dict[str, Any]] = {}
        logger.info(f"WorkflowProjectLoader initialized with path: {self.project_path}")

    def load_project(self):
        logger.info(f"Starting to load project from: {self.project_path}")
        if not os.path.exists(self.project_path):
            raise ValueError(f"Project path does not exist: {self.project_path}")

        workflow_files = self._find_workflow_files()
        for file_path in workflow_files:
            self._load_workflow_from_file(file_path)

        logger.info(f"Loaded {len(self.workflows)} workflows from Python files.")

    def _find_workflow_files(self) -> List[str]:
        workflow_files = []
        for root, dirs, files in os.walk(self.project_path):
            # Skip virtual environments, site-packages, and other unnecessary directories
            dirs[:] = [d for d in dirs if not self._should_skip_directory(d)]

            for file in files:
                if file.endswith(".py"):
                    file_path = os.path.join(root, file)
                    if self._is_workflow_file(file_path):
                        workflow_files.append(file_path)
        return workflow_files

    def _should_skip_directory(self, dir_name: str) -> bool:
        skip_dirs = {
            "venv",
            "env",
            ".venv",
            ".env",  # Virtual environments
            "site-packages",
            "dist-packages",  # Installed packages
            "__pycache__",
            ".git",
            ".idea",
            ".vscode",  # Cache and IDE directories
            "node_modules",  # Node.js modules
            "build",
            "dist",  # Build directories
        }
        return dir_name in skip_dirs or dir_name.startswith(".") or dir_name.endswith("egg-info")

    def _is_workflow_file(self, file_path: str) -> bool:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            return "StatefulWorkflow" in content and "create_" in content
        except UnicodeDecodeError:
            logger.warning(f"Skipping file due to encoding issues: {file_path}")
            return False
        except Exception as e:
            logger.warning(f"Error reading file {file_path}: {str(e)}")
            return False

    def _load_workflow_from_file(self, file_path: str):
        try:
            module_name = os.path.splitext(os.path.basename(file_path))[0]
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)

            for item_name in dir(module):
                if item_name.startswith("create_") and callable(getattr(module, item_name)):
                    workflow_func = getattr(module, item_name)
                    workflow_instance = workflow_func()
                    self.workflows[workflow_instance.name] = {
                        "name": workflow_instance.name,
                        "instance": workflow_instance,
                        "file": file_path,
                    }
                    logger.info(f"Loaded workflow '{workflow_instance.name}' from {file_path}")
        except Exception as e:
            logger.error(f"Error loading workflow from {file_path}: {str(e)}")

    def get_workflow(self, name: str) -> Dict[str, Any]:
        return self.workflows.get(name)

    def list_workflows(self) -> List[Dict[str, Any]]:
        return list(self.workflows.values())
