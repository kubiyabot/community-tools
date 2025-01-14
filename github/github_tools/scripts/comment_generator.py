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
        self.template_dir = Path(__file__).parent / 'templating' / 'templates'
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

def parse_failures(failures_json: str) -> list:
    """Parse workflow failures from JSON string."""
    try:
        return json.loads(failures_json)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid failures JSON: {e}")
        sys.exit(1)

def parse_fixes(fixes_json: str) -> list:
    """Parse workflow fixes from JSON string."""
    try:
        return json.loads(fixes_json)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid fixes JSON: {e}")
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
        Path(__file__).parent / 'templating' / 'templates' / 'workflow_failure.jinja2',
        Path(__file__).parent / 'utils' / 'templating' / 'templates' / 'workflow_failure.jinja2',
        # Check in /opt/scripts path (Docker container)
        Path('/opt/scripts/templating/templates/workflow_failure.jinja2'),
        Path('/opt/scripts/utils/templating/templates/workflow_failure.jinja2'),
    ]
    
    for path in possible_paths:
        if path.exists():
            logger.info(f"Found template at: {path}")
            return path
            
    raise FileNotFoundError("Could not find workflow_failure.jinja2 template in any expected location")

def combine_failures_and_fixes(failures, fixes):
    """
    Combine failures and suggested fixes into a list of dictionaries.
    Each dictionary contains:
    - step
    - error (failure)
    - fix_description
    - fix_code_sample
    """
    combined = []
    for failure, fix in zip(failures, fixes):
        combined.append({
            'step': failure['step'],
            'error': failure['error'],
            'fix_description': fix['description'],
            'fix_code_sample': fix['code_sample']
        })
    return combined

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
        failures = parse_failures(variables['failures'])
        fixes = parse_fixes(variables['fixes'])
        run_details = parse_run_details(variables['run_details'])
        
        # Create template context
        context = {
            'workflow_name': run_details.get('name', 'Unknown Workflow'),
            'failed_steps': [failure['step'] for failure in failures],
            'failures': failures,  # Pass the full failures list directly
            'fixes': fixes,  # Pass the full fixes list directly 
            'failures_and_fixes': combine_failures_and_fixes(failures, fixes),
            'workflow_steps': [step['name'] for step in workflow_steps],
            'error_logs': variables['error_logs'],
            'run_details': json.dumps(run_details),  # Pass as JSON string
            'number': variables['pr_number'],
            'repo': variables['repo']
        }
        # Process the context dictionary to replace escape sequences
        context = process_error_logs_in_context(context)

        context = {
            'workflow_name': 'CI Pipeline',
            'failed_steps': ['Intentional failure step'],
            'failures': [{'step': 'Intentional failure step', 'error': 'Process completed with exit code 1', 'file': '.github/workflows/main.yaml', 'line': 102}],
            'fixes': [{'step': 'Intentional failure step', 'description': 'Remove or correct the step that is designed to fail intentionally.', 'code_sample': "- name: Intentional failure step\n  run: exit 1\n# Suggest removal or corrective action to ensure it doesn't fail."}],
            'failures_and_fixes': [{'step': 'Intentional failure step', 'error': 'Process completed with exit code 1', 'fix_description': 'Remove or correct the step that is designed to fail intentionally.', 'fix_code_sample': "- name: Intentional failure step\n  run: exit 1\n# Suggest removal or corrective action to ensure it doesn't fail."}],
            'workflow_steps': ['Build'],
            'error_logs': 'build  Intentional failure step  2024-12-29T05:46:30.4588375Z This step will always fail\nbuild  Intentional failure step  2024-12-29T05:46:30.4541555Z ##[endgroup]\nbuild  Intentional failure step  2024-12-29T05:46:30.4541269Z LD_LIBRARY_PATH: /opt/hostedtoolcache/Python/3.9.20/x64/lib\nbuild  Intentional failure step  2024-12-29T05:46:30.4540927Z Python3_ROOT_DIR: /opt/hostedtoolcache/Python/3.9.20/x64\nbuild  Intentional failure step  2024-12-29T05:46:30.4591482Z ##[error]Process completed with exit code 1.\nbuild  Intentional failure step  2024-12-29T05:46:30.4591482Z ##[error]Process completed with exit code 1.',
            'run_details': '{"id": "12532922165", "name": "CI Pipeline", "status": "completed", "conclusion": "failure", "pr_details": {"additions": 1, "author": "Kubiya-Testing", "base_branch": "main", "changed_files": [{"additions": 0, "changes": 50, "deletions": 50, "filename": ".github/workflows/main.yaml", "patch": "@@ -102,53 +102,3 @@ jobs:\n           echo \\"Step outputs:\\"\n           echo \\"${{ toJson(steps) }}\\"\n         } > detailed_logs.txt\n-\n-    - name: Send notification\n-      if: failure()\n-      run: |\n-        # Check if the event is a pull request\n-        if [ \\"${{ github.event_name }}\\" = \\"pull_request\\" ]; then\n-          PR_NUMBER=\\"${{ github.event.pull_request.number }}\\"\n-          PR_TITLE=\\"${{ github.event.pull_request.title }}\\"\n-          PR_AUTHOR=\\"${{ github.event.pull_request.user.login }}\\"\n-          PR_BASE=\\"${{ github.event.pull_request.base.ref }}\\"\n-          PR_HEAD=\\"${{ github.event.pull_request.head.ref }}\\"\n-          PR_URL=\\"${{ github.event.pull_request.html_url }}\\"\n-        else\n-          PR_NUMBER=\\"N/A\\"\n-          PR_TITLE=\\"N/A\\"\n-          PR_AUTHOR=\\"N/A\\"\n-          PR_BASE=\\"N/A\\"\n-          PR_HEAD=\\"N/A\\"\n-          PR_URL=\\"N/A\\"\n-        fi\n-        LOGS=$(cat detailed_logs.txt)\n-        TRUNCATED_LOGS=\\"${LOGS:0:65000}\\"\n-        ESCAPED_LOGS=$(echo \\"$TRUNCATED_LOGS\\" | jq -sRr @json)\n-        ESCAPED_PR=$(echo \\"$PR_NUMBER\\" | jq -sRr @json)\n-        PAYLOAD=$(jq -n \\\\\n-                    --arg status \\"${{ job.status }}\\" \\\\\n-                    --arg repo \\"$GITHUB_REPOSITORY\\" \\\\\n-                    --arg workflow \\"$GITHUB_WORKFLOW\\" \\\\\n-                    --arg commit \\"$GITHUB_SHA\\" \\\\\n-                    --arg logs \\"$ESCAPED_LOGS\\" \\\\\n-                    --arg job_name \\"${{ github.job }}\\" \\\\\n-                    --arg run_id \\"${{ github.run_id }}\\" \\\\\n-                    --arg run_url \\"${{ github.server_url }}/${{ github.repository }}/actions/runs/${{ github.run_id }}\\" \\\\\n-                    --arg git_tag \\"${{ github.ref }}\\" \\\\\n-                    --arg triggered_by \\"${{ github.actor }}\\" \\\\\n-                    --arg branch \\"${{ github.ref }}\\" \\\\\n-                    --arg commit_message \\"${{ github.event.head_commit.message }}\\" \\\\\n-                    --arg event_name \\"${{ github.event_name }}\\" \\\\\n-                    --arg workflow_name \\"${{ github.workflow }}\\" \\\\\n-                    --arg runner_os \\"${{ runner.os }}\\" \\\\\n-                    --arg runner_arch \\"${{ runner.arch }}\\" \\\\\n-                    --arg pr_number PR_NUMBER \\\\\n-                    --arg pr_author PR_AUTHOR \\\\\n-                    --arg pr_base PR_BASE \\\\\n-                    --arg pr_head PR_HEAD \\\\\n-                    --arg pr_url PR_URL \\\\\n-                    \'{status: $status, repository: $repo, workflow: $workflow, commit: $commit, logs: $logs}\')\n-        curl -fsSL -X POST -H \\"Content-Type: application/json\\" \\\\\n-        -d \\"$PAYLOAD\\" \\\\\n-        https://webhooksource-kubiya.hooks.kubiya.ai:8443/s6VmK-pQMecFQJEYmxFlJF0-2XOpXuLeOWFOA4pwK00JuTJOhw6GJ9CIPtdu7ZD7dJtysFi53oNmUzB3DKDzsBUI0J5v", "previous_filename": null, "status": "modified"}, {"additions": 1, "changes": 1, "deletions": 0, "filename": "feature-list", "patch": "@@ -0,0 +1 @@\n+feature a", "previous_filename": null, "status": "added"}], "commits_count": 2, "created_at": "2024-12-22T14:50:39Z", "deletions": 50, "description": null, "head_branch": "feature-a", "labels": [], "title": "Create feature-list", "updated_at": "2024-12-26T10:57:49Z"}, "processed_at": "2024-12-29 05:47:39"}',
            'number': '3',
            'repo': 'Kubiya-Testing/KubiyaTesting'
        }

        logger.info(f"run_details: {context['run_details']}")

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
            'FAILURES', 'FIXES', 'ERROR_LOGS', 'RUN_DETAILS'
        ]
        
        variables = {}
        for var in required_vars:
            if var not in os.environ:
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
