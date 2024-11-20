import os
import sys
import uuid
import hashlib
import platform
import warnings
import importlib.util
from typing import Any, Dict, List, Tuple, Optional
from pathlib import Path

from kubiya_sdk.tools.models import Tool
from kubiya_sdk.utils.logger import sdk_logger
from kubiya_sdk.tools.registry import tool_registry
from kubiya_sdk.kubiya_cli.bundle.models import BundleModel
from kubiya_sdk.workflows.stateful_workflow import StatefulWorkflow


def read_file_content(file_path: str) -> str:
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            return file.read()
    except Exception as e:
        sdk_logger.log(
            f"Error reading file {file_path}: {str(e)}",
            component="discovery",
            level="ERROR",
        )
        return ""


def get_requirements(package_path: str) -> List[str]:
    req_file = os.path.join(package_path, "requirements.txt")
    if not os.path.exists(req_file):
        return []
    try:
        with open(req_file, "r", encoding="utf-8") as f:
            requirements = [line.strip() for line in f if line.strip() and not line.startswith("#")]
        return requirements
    except Exception as e:
        sdk_logger.log(
            f"Error reading requirements file: {str(e)}",
            component="discovery",
            level="ERROR",
        )
        return []


def add_to_python_path(path: str):
    if path not in sys.path:
        sys.path.insert(0, path)


def is_package_directory(path: str) -> bool:
    return os.path.isfile(os.path.join(path, "__init__.py"))


def discover_python_files(source: str, ignore_patterns: List[str]) -> List[str]:
    python_files = []
    for root, dirs, files in os.walk(source):
        dirs[:] = [d for d in dirs if not any(ignore_pattern in d for ignore_pattern in ignore_patterns)]
        if is_package_directory(root):
            add_to_python_path(root)
        python_files.extend(
            os.path.join(root, f) for f in files if f.endswith(".py") and not f.startswith("__") and f != "setup.py"
        )
    return python_files


def create_isolated_environment():
    original_sys_path = sys.path.copy()
    original_sys_modules = sys.modules.copy()

    # Clear sys.path except for the current discovery source
    sys.path = []

    return original_sys_path, original_sys_modules


def restore_environment(original_sys_path, original_sys_modules):
    sys.path = original_sys_path
    sys.modules.clear()
    sys.modules.update(original_sys_modules)


def process_file(file_path: str, source: str) -> Tuple[List[Dict[str, Any]], List[Tool], Optional[Dict[str, Any]]]:
    relative_path = os.path.relpath(file_path, source)
    module_name = os.path.splitext(relative_path.replace(os.path.sep, "."))[0]

    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)

        workflows = []
        tools = []

        # Collect workflows from the module
        for name, obj in module.__dict__.items():
            if isinstance(obj, StatefulWorkflow):
                workflows.append(
                    {
                        "name": obj.name,
                        "diagram": obj.to_mermaid(),
                        "description": obj.description,
                        "entry_point": obj.entry_point,
                        "steps": list(obj.steps.keys()),
                        "metadata": obj.__dict__.get("metadata", {}),
                        "input_schema": obj.__dict__.get("input_schema", {}),
                        "source_file": relative_path,
                        "source_module": module_name,
                    }
                )

        # Collect tools from the module
        for _, tools_dict in tool_registry.tools.items():
            for tool_name, tool_obj in tools_dict.items():
                try:
                    tool = (
                        Tool(**tool_obj)
                        if isinstance(tool_obj, dict)
                        else Tool(
                            **{
                                attr: getattr(tool_obj, attr)
                                for attr in dir(tool_obj)
                                if not attr.startswith("_") and not callable(getattr(tool_obj, attr))
                            }
                        )
                    )
                    if not tool.mermaid:
                        sdk_logger.log(
                            f"Tool {tool_name} doesn't have a mermaid diagram. Generating one...",
                            component="discovery",
                            level="WARNING",
                        )
                        tool.mermaid = tool.to_mermaid()
                    tools.append(tool)
                except Exception as tool_error:
                    sdk_logger.log(
                        f"Error processing tool {tool_name} in file {file_path}: {str(tool_error)}",
                        component="discovery",
                        level="ERROR",
                    )

        return workflows, tools, None
    except ImportError as e:
        sdk_logger.log(
            f"ImportError in file {relative_path}: {str(e)}",
            component="discovery",
            level="ERROR",
        )
        return (
            [],
            [],
            {
                "file": relative_path,
                "error": str(e),
                "error_type": type(e).__name__,
                "suggestion": "Check if all required modules are installed and accessible.",
            },
        )
    except Exception as e:
        sdk_logger.log(
            f"Unexpected error in file {relative_path}: {str(e)}",
            component="discovery",
            level="ERROR",
        )
        return (
            [],
            [],
            {
                "file": relative_path,
                "error": str(e),
                "error_type": type(e).__name__,
            },
        )


def deduplicate_tools(tools: List[Tool]) -> List[Tool]:
    unique_tools = {}
    for tool in tools:
        if tool.name not in unique_tools:
            unique_tools[tool.name] = tool
    return list(unique_tools.values())


def clear_tool_registry():
    """Clear the tool registry to ensure the discovery is stateless."""
    tool_registry.tools.clear()


def log_error_summary(errors: List[Dict[str, Any]]):
    if errors:
        sdk_logger.log(
            f"Encountered {len(errors)} errors during discovery.",
            component="discovery",
            level="ERROR",
        )
        for error in errors:
            sdk_logger.log(
                f"Error in file {error.get('file', 'unknown')}: {error.get('error', 'unknown error')}",
                component="discovery",
                level="ERROR",
            )
            sdk_logger.log(
                f"Error type: {error.get('error_type', 'unknown type')}",
                component="discovery",
                level="ERROR",
            )
            if "suggestion" in error:
                sdk_logger.log(
                    f"Suggestion: {error['suggestion']}",
                    component="discovery",
                    level="INFO",
                )


def discover_workflows_and_tools(source: str, source_url: Optional[str] = None) -> Dict[str, Any]:
    # temp_dir = None
    # commit_info = None
    source_info = {
        "id": str(uuid.uuid4()),  # Generate a UUID for each discovery run
        "hash": hashlib.md5(source.encode()).hexdigest(),
    }
    if source_url:
        source_info["url"] = source_url

    if os.path.isdir(source):
        source_info["directory"] = os.path.abspath(source)
    else:
        return {
            "error": "Invalid source",
            "message": "The provided source must be a directory, file, or a Git URL.",
        }

    bundle_json = Path(source) / "kubiya_bundle.json"
    if bundle_json.exists():
        sdk_logger.log(f"Found kubiya_bundle.json in source: {source}", component="discovery")
        bundle_json_content = bundle_json.read_text()
        try:
            bundle = BundleModel.model_validate_json(bundle_json_content)
        except Exception as e:
            sdk_logger.log(
                f"Error processing bundle file: {str(e)}",
                component="discovery",
                level="ERROR",
            )
            return {
                "python_version": platform.python_version(),
                "package_name": os.path.basename(source),
                "package_root_path": source,
                "workflows": [],
                "tools": [],
                "errors": [str(e)],
                "source": source_info,
            }

        return {
            "python_version": platform.python_version(),
            "package_name": os.path.basename(source),
            "package_root_path": source,
            "workflows": [],
            "tools": bundle.tools,
            "errors": bundle.errors,
            "source": source_info,
        }

    # Set up isolated environment
    original_sys_path, original_sys_modules = create_isolated_environment()

    # Clear the tool registry to make the discovery stateless
    clear_tool_registry()

    add_to_python_path(source)
    python_files = discover_python_files(
        source, ["venv", "env", ".venv", ".env", "site-packages", "__pycache__", ".git"]
    )

    if not python_files:
        return {
            "error": "No Python files found",
            "message": "The provided source does not contain any valid Python files.",
        }

    workflows, tools, errors = [], [], []

    for file_path in python_files:
        try:
            file_workflows, file_tools, error = process_file(file_path, source)
            workflows.extend(file_workflows)
            tools.extend(file_tools)
            if error:
                errors.append(error)
        except Exception as e:
            sdk_logger.log(
                f"Error processing file {file_path}: {str(e)}",
                component="discovery",
                level="ERROR",
            )
            errors.append({"file": file_path, "error": str(e), "error_type": type(e).__name__})

    tools = deduplicate_tools(tools)

    result = {
        "python_version": platform.python_version(),
        "package_name": os.path.basename(source),
        "package_root_path": source,
        "workflows": workflows,
        "tools": [tool.dict(exclude_unset=True) for tool in tools],
        "errors": errors,
        "source": source_info,
    }

    if not workflows and not tools:
        result["warning"] = "No workflows or tools were discovered in the package."

    # Log error summary if there are any errors
    log_error_summary(errors)

    # Restore the environment
    restore_environment(original_sys_path, original_sys_modules)

    return result


def run_discovery(source: str, source_url: Optional[str] = None):
    try:
        result = discover_workflows_and_tools(source, source_url)
        sdk_logger.log(f"Discovery result: {result}", component="discovery")
    except Exception as e:
        sdk_logger.log(
            f"An error occurred during discovery: {str(e)}",
            component="discovery",
            level="ERROR",
        )


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python discovery.py <source> [source_url]")
        sys.exit(1)

    source = sys.argv[1]
    source_url = sys.argv[2] if len(sys.argv) > 2 else None
    run_discovery(source, source_url)
