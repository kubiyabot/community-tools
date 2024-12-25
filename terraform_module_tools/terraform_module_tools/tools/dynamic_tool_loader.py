from typing import Dict, Any, List, Optional
from kubiya_sdk.tools import Tool
from kubiya_sdk.tools.registry import tool_registry
import logging
from pathlib import Path
from .terraformer_tool import TerraformerTool, _initialize_provider_tools
from .module_tools import initialize_module_tools
from ..scripts.error_handler import handle_script_error, ScriptError

logger = logging.getLogger(__name__)

class DynamicToolLoader:
    """Dynamically load and initialize terraform tools based on configuration."""

    @classmethod
    def load_tools(cls, config: Optional[Dict[str, Any]] = None) -> List[Tool]:
        """Load and initialize tools based on configuration."""
        tools = []
        try:
            if not config:
                logger.warning("No configuration provided for tool loading")
                return tools

            # Initialize terraformer tools if enabled
            if config.get('terraform', {}).get('enable_reverse_terraform'):
                logger.info("🔄 Loading terraformer tools...")
                providers = TerraformerTool.get_enabled_providers(config)
                
                for provider in providers:
                    try:
                        provider_tools = _initialize_provider_tools(provider)
                        if provider_tools:
                            for tool in provider_tools:
                                tools.append(tool)
                                tool_registry.register("terraform", tool)
                                logger.info(f"✅ Registered tool: {tool.name}")
                    except Exception as e:
                        logger.error(f"Failed to initialize tools for provider {provider}: {str(e)}")

            # Initialize module tools if configured
            if config.get('terraform', {}).get('modules'):
                logger.info("📦 Loading module tools...")
                try:
                    module_tools = initialize_module_tools(config)
                    if module_tools:
                        for tool in module_tools.values():
                            tools.append(tool)
                            tool_registry.register("terraform", tool)
                            logger.info(f"✅ Registered module tool: {tool.name}")
                except Exception as e:
                    logger.error(f"Failed to initialize module tools: {str(e)}")

            if not tools:
                logger.warning("⚠️ No tools were loaded")
            else:
                logger.info(f"🎉 Successfully loaded {len(tools)} tools")

            return tools

        except Exception as e:
            logger.error(f"Error loading tools: {str(e)}")
            return tools

    @classmethod
    def get_tool_config(cls, tool_name: str) -> Dict[str, Any]:
        """Get tool configuration with proper defaults."""
        try:
            base_config = {
                'type': 'docker',
                'image': 'hashicorp/terraform:latest',
                'mermaid': {
                    'graph': f"""
                        graph TD
                            A[Start] --> B[{tool_name}]
                            B --> C[Execute Command]
                            C --> D[Return Result]
                    """
                }
            }

            if 'import' in tool_name:
                base_config.update({
                    'description': 'Import existing infrastructure into Terraform code',
                    'steps': [
                        'Validate input parameters',
                        'Create output directory',
                        'Run terraformer import command',
                        'Return results'
                    ]
                })
            elif 'scan' in tool_name:
                base_config.update({
                    'description': 'Scan and discover infrastructure for Terraform import',
                    'steps': [
                        'Validate input parameters',
                        'Run terraformer scan command',
                        'Process and return results'
                    ]
                })

            return base_config

        except Exception as e:
            logger.error(f"Error getting tool config for {tool_name}: {str(e)}")
            return {}

__all__ = ['DynamicToolLoader']

