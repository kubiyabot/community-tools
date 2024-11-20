import os
import sys
import platform
import importlib
import traceback
import importlib.util
import importlib.machinery
from pathlib import Path
from contextlib import contextmanager

from kubiya_sdk.tools.models import Tool
from kubiya_sdk.utils.logger import sdk_logger
from kubiya_sdk.tools.registry import tool_registry

from .models import BundleModel, DiscoveryError


class CustomModuleLoader:
    def __init__(self, directory):
        self.directory = directory

    def load_module(self, fullname):
        if fullname in sys.modules:
            return sys.modules[fullname]

        parts = fullname.split(".")
        path = self.directory
        for part in parts:
            path = os.path.join(path, part)

        if os.path.isdir(path):
            path = os.path.join(path, "__init__.py")
        else:
            path += ".py"

        if not os.path.exists(path):
            raise ImportError(f"No module named '{fullname}'")

        spec = importlib.util.spec_from_file_location(fullname, path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[fullname] = module
        spec.loader.exec_module(module)

        return module


class CustomPathFinder:
    def __init__(self, directory):
        self.directory = directory
        self.loader = CustomModuleLoader(directory)

    def find_spec(self, fullname, path, target=None):
        parts = fullname.split(".")
        path = self.directory
        for part in parts:
            path = os.path.join(path, part)

        if os.path.isdir(path) or os.path.exists(path + ".py"):
            return importlib.machinery.ModuleSpec(fullname, self.loader)

        return None


@contextmanager
def add_custom_importer(directory):
    custom_finder = CustomPathFinder(directory)
    sys.meta_path.insert(0, custom_finder)
    try:
        yield
    finally:
        sys.meta_path.remove(custom_finder)


def import_module_from_path(module_path, module_name):
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def import_all_modules(directory, ignore_dirs: tuple[str] = tuple()) -> list[DiscoveryError]:
    errors: list[DiscoveryError] = []
    with add_custom_importer(directory):
        for root, dirs, files in os.walk(directory):
            directories_to_ignore = ignore_dirs + (".venv", "venv")
            for dir_to_remove in directories_to_ignore:
                if dir_to_remove in dirs:
                    sdk_logger.log(
                        f"Removing {dir_to_remove} from dirs",
                        component="discovery",
                        level="INFO",
                    )
                    dirs.remove(dir_to_remove)
            for file in files:
                if file.endswith(".py") and not file.startswith("__"):
                    module_path = os.path.join(root, file)
                    sdk_logger.log(
                        f"Importing {module_path}",
                        component="discovery",
                        level="DEBUG",
                    )
                    module_name = os.path.relpath(os.path.splitext(module_path)[0], directory).replace(os.path.sep, ".")
                    try:
                        import_module_from_path(module_path, module_name)
                        sdk_logger.log(
                            f"Imported {module_path}",
                            component="discovery",
                            level="DEBUG",
                        )
                    except Exception as e:
                        error = f"Failed to import {module_path}: {e}"
                        sdk_logger.log(
                            error,
                            component="discovery",
                            level="WARNING",
                        )
                        errors.append(DiscoveryError(file=module_path, error=error, error_type=str(type(e))))

    return errors


def get_tools(base_dir: str, ignore_dirs: tuple[str] = tuple()) -> tuple[list[Tool], list[DiscoveryError]]:
    sdk_logger.log(
        f"Discovering workflows and tools in directory: {base_dir}",
        component="discovery",
    )
    errors: list[DiscoveryError] = []
    try:
        import_errors = import_all_modules(base_dir, ignore_dirs)
    except BaseException as e:
        traceback.print_exc()
        sdk_logger.log(
            "Exception while importing modules",
            component="Bundle",
            level="ERROR",
        )
        raise RuntimeError("Failed to import modules") from e

    errors.extend(import_errors)
    tools = []
    for _, tools_dict in tool_registry.tools.items():
        for tool_name, tool in tools_dict.items():
            try:
                if not tool.mermaid:
                    sdk_logger.log(
                        f"Tool {tool_name} doesn't have a mermaid diagram. Generating one...",
                        component="discovery",
                        level="WARNING",
                    )
                    tool.mermaid = tool.to_mermaid()
                tools.append(tool)
            except Exception as tool_error:
                msg = f"Error processing tool {tool_name}: {str(tool_error)}"
                sdk_logger.log(
                    msg,
                    component="discovery",
                    level="ERROR",
                )
                errors.append(DiscoveryError(file=tool_name, error=msg, error_type=str(type(tool_error))))
    return tools, errors


def bundle(base_dir: str, ignore_dirs: tuple[str] = tuple(), save_to_file: bool = False) -> BundleModel:
    tools, errors = get_tools(base_dir, ignore_dirs)

    bundle = BundleModel(
        tools=tools,
        errors=errors,
        python_bundle_version=platform.python_version(),
    )

    if save_to_file:
        bundle_file = Path(base_dir) / "kubiya_bundle.json"
        sdk_logger.log(
            f"Saving bundle file: {base_dir}",
            component="discovery",
        )
        try:
            bundle_file.write_text(bundle.model_dump_json(indent=2))
        except Exception as e:
            sdk_logger.log(
                f"Failed to write bundle file to {bundle_file}: {str(e)}",
                component="discovery",
                level="ERROR",
            )

    return bundle
