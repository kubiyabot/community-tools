import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional
import json

try:
    from jinja2 import Environment, FileSystemLoader, select_autoescape
except ImportError:
    print("⚠️  Import Warning:")
    print("   Could not import jinja2.")
    print("   This is expected during discovery phase and can be safely ignored.")
    print("   The required modules will be available during actual execution.")
    pass

logger = logging.getLogger(__name__)

class TemplateHandler:
    def __init__(self):
        self.template_dir = Path(__file__).parent / 'templates'
        self.env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            autoescape=select_autoescape(['html', 'xml']),
            trim_blocks=True,
            lstrip_blocks=True
        )
        # Add JSON filter
        self.env.filters['from_json'] = json.loads

    def render_template(self, template_name: str, variables: Dict[str, Any]) -> Optional[str]:
        """Render a template with given variables."""
        try:
            template = self.env.get_template(f"{template_name}.jinja2")
            logger.info(f"Template '{template_name}' found and loaded")
            try:
                result = template.render(**variables)
                logger.info("Template rendered successfully")
                return result
            except Exception as e:
                logger.error(f"Template rendering failed: {str(e)}")
                logger.error(f"Template variables: {variables}")
                raise
        except Exception as e:
            logger.error(f"Failed to load template {template_name}: {str(e)}")
            return None

    def get_available_templates(self) -> list:
        """Get list of available templates."""
        try:
            return [f.stem for f in self.template_dir.glob('*.jinja2')]
        except Exception as e:
            logger.error(f"Failed to list templates: {str(e)}")
            return [] 