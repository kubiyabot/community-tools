#!/usr/bin/env python
from datetime import datetime
try:
    import jinja2
except ImportError:
    print("⚠️  Import Warning:")
    print("   Could not import jinja2.")
    print("   This is expected during discovery phase and can be safely ignored.")
    print("   The required modules will be available during actual execution.")
    pass
import os
import sys
import json
from pathlib import Path
from typing import Dict, Any, Optional

try:
    from jinja2 import Environment, FileSystemLoader, select_autoescape
except ImportError:
    print("⚠️  Import Warning:")
    print("   Could not import jinja2.")
    print("   This is expected during discovery phase and can be safely ignored.")
    print("   The required modules will be available during actual execution.")
    pass

class TemplateHandler:
    def __init__(self):
        self.template_dir = Path(__file__).parent / 'templates'
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
            try:
                result = template.render(**variables)
                return result
            except Exception:
                raise
        except Exception:
            return None

    def get_available_templates(self) -> list:
        """Get list of available templates."""
        try:
            return [f.stem for f in self.template_dir.glob('*.jinja2')]
        except Exception:
            return [] 


def parse_workflow_steps(steps_json: str) -> list:
    """Parse workflow steps from JSON string."""
    try:
        return json.loads(steps_json)
    except json.JSONDecodeError:
        # Return empty list instead of exiting
        return []

def find_template_file() -> Path:
    """Find the workflow failure template file."""
    possible_paths = [
        # Check relative to script location
        Path(__file__).parent / 'templates' / 'workflow_failure.jinja2',
        # Check in /opt/scripts path (Docker container)
        Path('/opt/scripts/templates/workflow_failure.jinja2'),
    ]
    
    for path in possible_paths:
        if path.exists():
            return path
            
    raise FileNotFoundError("Could not find workflow_failure.jinja2 template in any expected location")

def generate_comment(variables: dict) -> str:
    """Generate a comment using the workflow failure template."""
    try:
        # Parse workflow steps
        workflow_steps = parse_workflow_steps(variables['workflow_steps'])
        
        # Create template context
        context = {
            'workflow_steps': workflow_steps,
            'failures_and_fixes': variables['failures_and_fixes'],  # Use as is without parsing
            'number': variables['pr_number'],
            'repo': variables['repo'],
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')
        }

        # Initialize template handler
        template_handler = TemplateHandler()

        # Render the template
        comment = template_handler.render_template('workflow_failure', context)

        if not comment:
            raise ValueError("Failed to generate comment from template")
            
        return comment

    except Exception as e:
        print(f"Error generating comment: {str(e)}")
        sys.exit(1)

def main():
    """Main function to handle comment generation."""
    try:
        # Get variables from environment
        required_vars = [
            'REPO', 'PR_NUMBER', 'WORKFLOW_STEPS', 
            'FAILURES_AND_FIXES'
        ]
        
        variables = {}
        for var in required_vars:
            if var not in os.environ:
                print(f"Missing required environment variable: {var}")
                raise KeyError(f"Missing required environment variable: {var}")
            variables[var.lower()] = os.environ[var]
        
        comment = generate_comment(variables)
        print(comment)
        
    except KeyError as e:
        print(f"Missing environment variable: {str(e)}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()