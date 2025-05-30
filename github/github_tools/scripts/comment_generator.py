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
            'workflow_failure_summary': variables.get('workflow_failure_summary', 'Workflow failed with errors'),
            'workflow_failure_reason': variables.get('workflow_failure_reason', 'See detailed error logs'),
            'workflow_failure_fixes': variables.get('workflow_failure_fixes', 'Fix the issues identified in the error logs'),
            'recommended_fix': variables.get('recommended_fix', 'Detailed instructions:\n1. Review the error logs carefully\n2. Address each error according to the guidance above\n3. Commit and push your changes\n4. Re-run the workflow'),
            'detailed_error_logs': variables.get('detailed_error_logs', 'No detailed logs available'),
            'run_details': f"PR #{variables['pr_number']} in {variables['repo']}",
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
            'REPO', 'PR_NUMBER', 
            'WORKFLOW_FAILURE_SUMMARY', 'WORKFLOW_FAILURE_REASON', 'WORKFLOW_FAILURE_FIXES',
            'RECOMMENDED_FIX', 'DETAILED_ERROR_LOGS'
        ]
        
        # Map environment variable names to context variable names
        env_to_context = {
            'WORKFLOW_FAILURE_SUMMARY': 'workflow_failure_summary',
            'WORKFLOW_FAILURE_REASON': 'workflow_failure_reason',
            'WORKFLOW_FAILURE_FIXES': 'workflow_failure_fixes',
            'RECOMMENDED_FIX': 'recommended_fix',
            'DETAILED_ERROR_LOGS': 'detailed_error_logs',
            'REPO': 'repo',
            'PR_NUMBER': 'pr_number'
        }
        
        variables = {}
        
        # Add required variables
        for var in required_vars:
            if var not in os.environ:
                print(f"Missing required environment variable: {var}")
                raise KeyError(f"Missing required environment variable: {var}")
            variables[env_to_context[var]] = os.environ[var]
        
        # Set default empty workflow steps
        variables['workflow_steps'] = '[]'
        
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