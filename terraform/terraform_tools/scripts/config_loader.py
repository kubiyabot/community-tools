import yaml
import logging
from pathlib import Path
from typing import Dict, Any, Union
from .module_scanner import TerraformModuleScanner
import re

logger = logging.getLogger(__name__)

class ModuleLoader:
    def __init__(self):
        self.scanner = TerraformModuleScanner()
        self.modules_dir = Path(__file__).parent.parent / 'modules'

    def _load_yaml(self, file_path: Path) -> Dict[str, Any]:
        """Load and parse a YAML file."""
        try:
            with open(file_path) as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Error loading {file_path}: {e}")
            raise

    def _process_module(self, module_path: Path, provider: str, category: str) -> Dict[str, Any]:
        """Process a single module file."""
        try:
            config = self._load_yaml(module_path)
            module_name = f"{provider}_{category}_{module_path.stem}"
            
            # Handle module source if present
            if "source" in config:
                source_info = {
                    "type": "registry" if "/" in config["source"] else "git",
                    "url": config["source"]
                }
                
                if "version" in config:
                    source_info["ref"] = config["version"]
                
                # Auto-discover variables if enabled
                if config.get("auto_discover", False):
                    scan_result = self.scanner.scan_module(
                        source_type=source_info["type"],
                        source_url=source_info["url"],
                        ref=source_info.get("ref")
                    )
                    
                    # Merge scanned variables with defined ones
                    variables = scan_result["variables"]
                    for var_name, var_config in config.get("variables", {}).items():
                        if var_name in variables:
                            variables[var_name].update(var_config)
                        else:
                            variables[var_name] = var_config
                            
                    config["variables"] = variables
                    config["outputs"] = scan_result["outputs"]
                    config["examples"] = scan_result["examples"]
                
            return {
                module_name: {
                    **config,
                    "provider": provider,
                    "category": category,
                    "file_path": str(module_path)
                }
            }
            
        except Exception as e:
            logger.error(f"Error processing module {module_path}: {e}")
            return {}

    def load_all_modules(self) -> Dict[str, Any]:
        """Load all module configurations from the modules directory."""
        all_modules = {}
        
        # Scan through provider directories
        for provider_dir in self.modules_dir.iterdir():
            if provider_dir.is_dir():
                provider = provider_dir.name
                
                # Scan through category directories
                for category_dir in provider_dir.iterdir():
                    if category_dir.is_dir():
                        category = category_dir.name
                        
                        # Load all YAML files in the category
                        for module_file in category_dir.glob("*.yaml"):
                            module_config = self._process_module(module_file, provider, category)
                            all_modules.update(module_config)
        
        return all_modules

def load_terraform_configs() -> Dict[str, Any]:
    """Load and validate all Terraform module configurations."""
    try:
        loader = ModuleLoader()
        return loader.load_all_modules()
    except Exception as e:
        logger.error(f"Error loading Terraform configurations: {e}")
        raise

__all__ = ['load_terraform_configs'] 