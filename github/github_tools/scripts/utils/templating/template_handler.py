import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from jinja2 import Environment, FileSystemLoader, select_autoescape

logger = logging.getLogger(__name__)

class TemplateHandler:
    def __init__(self, template_dir: Optional[str] = None):
        """Initialize template handler with optional custom template directory."""
        self.template_dir = Path(template_dir) if template_dir else Path(__file__).parent / 'templates'
        self.env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            autoescape=select_autoescape(['html', 'xml']),
            trim_blocks=True,
            lstrip_blocks=True
        )

    def render_template(self, template_name: str, variables: Dict[str, Any]) -> Optional[str]:
        """Render a template with given variables."""
        try:
            template = self.env.get_template(f"{template_name}.jinja2")
            return template.render(**variables)
        except Exception as e:
            logger.error(f"Failed to render template {template_name}: {str(e)}")
            return None

    def get_available_templates(self) -> list:
        """Get list of available templates."""
        try:
            return [f.stem for f in self.template_dir.glob('*.jinja2')]
        except Exception as e:
            logger.error(f"Failed to list templates: {str(e)}")
            return [] 