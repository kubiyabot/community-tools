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
import logging
from pathlib import Path
from typing import Dict, Any, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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


def parse_workflow_steps(steps_json: str) -> list:
    """Parse workflow steps from JSON string."""
    try:
        return json.loads(steps_json)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid workflow steps JSON: {e}")
        sys.exit(1)

def parse_failures_and_fixes(failures_and_fixes_json: str) -> list:
    """Parse workflow failures and fixes from JSON string."""
    try:
        return json.loads(failures_and_fixes_json)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid failures and fixes JSON: {e}")
        sys.exit(1)

def parse_run_details(details_json: str) -> dict:
    """Parse workflow run details from JSON string."""
    try:
        _detailes_json = json.loads(details_json)
        _detailes_json['processed_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        return _detailes_json
    except json.JSONDecodeError as e:
        logger.error(f"Invalid run details JSON: {e}")
        sys.exit(1)

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
            logger.info(f"Found template at: {path}")
            return path
            
    raise FileNotFoundError("Could not find workflow_failure.jinja2 template in any expected location")

def process_error_logs_in_context(context):
    """
    Recursively processes all values in the dictionary context to replace
    escape sequences (\t and \n) with actual tabs and newlines.
    """
    for key, value in context.items():
        if isinstance(value, str):
            # Replace the escape sequences with actual tabs and newlines
            context[key] = value.replace(r'\t', '\t').replace(r'\n', '\n')
        elif isinstance(value, dict):
            # Recursively process nested dictionaries
            process_error_logs_in_context(value)
        elif isinstance(value, list):
            # Process lists (apply to each element in the list if it's a string)
            for i, item in enumerate(value):
                if isinstance(item, str):
                    value[i] = item.replace(r'\t', '\t').replace(r'\n', '\n')
                elif isinstance(item, dict):
                    process_error_logs_in_context(item)
    return context

def generate_comment(variables: dict) -> str:
    """Generate a comment using the workflow failure template."""
    try:
        # Parse JSON inputs
        workflow_steps = parse_workflow_steps(variables['workflow_steps'])
        run_details = parse_run_details(variables['run_details'])
        failures_and_fixes = parse_failures_and_fixes(variables['failures_and_fixes'])
        
        # Create template context
        context = {
            'workflow_steps': workflow_steps,
            'failures_and_fixes': failures_and_fixes,
            'error_logs': variables['error_logs'],
            'run_details': json.dumps(run_details),  # Pass as JSON string
            'number': variables['pr_number'],
            'repo': variables['repo']
        }
        # Process the context dictionary to replace escape sequences
        context = process_error_logs_in_context(context)

        # Now the processed_context contains the updated values with actual tabs and newlines
        logger.info(f"context: {context}")

        # Initialize template handler
        template_handler = TemplateHandler()

        logger.info(f"Available templates: {template_handler.get_available_templates()}")

        # Render the template
        comment = template_handler.render_template('workflow_failure', context)

        if not comment:
            raise ValueError("Failed to generate comment from template")
            
        logger.info("Successfully generated comment")
        return comment

    except Exception as e:
        logger.error(f"Error generating comment: {str(e)}")
        sys.exit(1)

def main():
    """Main function to handle comment generation."""
    try:
        # Get variables from environment
        required_vars = [
            'REPO', 'PR_NUMBER', 'WORKFLOW_STEPS', 
            'FAILURES_AND_FIXES', 'ERROR_LOGS', 'RUN_DETAILS'
        ]
        
        variables = {}
        for var in required_vars:
            if var not in os.environ:
                print(f"Missing required environment variable: {var}")
                raise KeyError(f"Missing required environment variable: {var}")
            variables[var.lower()] = os.environ[var]
        
        logger.info("Starting comment generation...")
        comment = generate_comment(variables)
        print(comment)
        logger.info("Comment generation completed successfully")
        
    except KeyError as e:
        logger.error(f"Missing environment variable: {str(e)}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()