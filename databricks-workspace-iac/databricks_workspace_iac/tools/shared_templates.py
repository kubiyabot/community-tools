import json
import os
from databricks_workspace_iac.tools.constants import DATABRICKS_ICON_URL

# Function to create Terraform variable dictionaries
def tf_var(name, description, required=False, default=None):
    return {
        "name": name,
        "description": description,
        "required": required,
        "default": default
    }

# Git clone command for fetching Terraform configurations
GIT_CLONE_COMMAND = 'git clone -b "$BRANCH" "https://$PAT@github.com/$GIT_ORG/$GIT_REPO.git" "iac_workspace"'

# Common workspace creation template
COMMON_WORKSPACE_TEMPLATE = """
#!/bin/bash
# We're running Terraform in a container, so we don't need color output
# We're also not running Terraform interactively, so we don't need interactive input
export TERRAFORM_NO_COLOR=true
export TF_INPUT=false
set -euo pipefail

apk add jq curl git --quiet

echo -e "🛠️ Setting up Databricks workspace on {CLOUD_PROVIDER}..."
{GIT_CLONE_COMMAND}

# Navigate to the cloned repository, then to the Terraform module directory
cd iac_workspace/${TERRAFORM_MODULE_PATH}

echo -e "🔍 Validating input parameters..."

# Function to check if a variable is set
check_var() {
    if [ -z "${1:-}" ]; then
        echo "❌ Error: $1 is not set. Please provide it as an argument or environment variable."
        echo "Could not apply Terraform workspace. Please provide the necessary variables and try again."
        exit 1
    fi
}

# Check required variables
{CHECK_REQUIRED_VARS}

echo -e "✅ All required parameters are set."

echo -e "🚀 Initializing Terraform..."
{TERRAFORM_INIT_COMMAND}

echo -e "🏗️ Applying Terraform configuration..."
# Create a JSON file with Terraform variables
cat << EOF > terraform.tfvars.json
{TERRAFORM_VARS_JSON}
EOF

terraform apply -auto-approve -var-file=terraform.tfvars.json

echo "📊 Capturing Terraform output..."
tf_output=$(terraform output -json || echo "{{}}")
workspace_url=$(echo "$tf_output" | jq -r '.databricks_host.value // empty')
workspace_url="${{workspace_url:-"{FALLBACK_WORKSPACE_URL}"}}"

echo "🔍 Getting backend config..."
backend_config=$(terraform show -json | jq -r '.values.backend_config // empty')

echo "💬 Preparing Slack message..."
SLACK_MESSAGE_CONTENT=$(cat <<EOF
{{
    "blocks": [
        {{
            "type": "context",
            "elements": [
                {{
                    "type": "image",
                    "image_url": "${DATABRICKS_ICON_URL}",
                    "alt_text": "Databricks Logo"
                }},
                {{
                    "type": "mrkdwn",
                    "text": "🔧 Your *Databricks workspace* was provisioned using *Terraform*, following *Infrastructure as Code (IAC)* best practices for smooth future changes and management. *Going forward*, you can easily manage and track updates on your infrastructure. *Module Source code*: <{GIT_REPO}|Explore the module>"
                }}
            ]
        }},
        {{
            "type": "section",
            "text": {{
                "type": "mrkdwn",
                "text": "*To import the state locally, follow these steps:*\\n1. Configure your Terraform backend:\\n\`\`\`\\nterraform {{\\n  backend \\"{BACKEND_TYPE}\\" {{\\n    $backend_config\\n  }}\\n}}\\n\`\`\`\\n2. Run the import command:\\n\`\`\`\\n{IMPORT_COMMAND}\\n\`\`\`"
            }}
        }}
    ]
}}
EOF
)

echo -e "📤 Sending Slack message..."
curl -X POST "https://slack.com/api/chat.postMessage" \
-H "Authorization: Bearer $SLACK_API_TOKEN" \
-H "Content-Type: application/json" \
--data "$SLACK_MESSAGE_CONTENT"

echo -e "✅ Databricks workspace setup complete!"
"""

# Error notification template
ERROR_NOTIFICATION_TEMPLATE = """
SLACK_ERROR_MESSAGE_CONTENT=$(cat <<EOF
{{
    "blocks": [
        {{
            "type": "header",
            "text": {{
                "type": "plain_text",
                "text": "❌ Error: Databricks Workspace Creation Failed",
                "emoji": true
            }}
        }},
        {{
            "type": "section",
            "text": {{
                "type": "mrkdwn",
                "text": "An error occurred while creating the Databricks workspace on {CLOUD_PROVIDER}. Please check the logs for more details."
            }}
        }},
        {{
            "type": "section",
            "text": {{
                "type": "mrkdwn",
                "text": "*Error Message:*\\n\`\`\`$1\`\`\`"
            }}
        }}
    ]
}}
EOF
)

curl -X POST "https://slack.com/api/chat.postMessage" \
-H "Authorization: Bearer $SLACK_API_TOKEN" \
-H "Content-Type: application/json" \
--data "$SLACK_ERROR_MESSAGE_CONTENT"
"""

# Wrap the workspace template with error handling
WORKSPACE_TEMPLATE_WITH_ERROR_HANDLING = """
#!/bin/bash
set -euo pipefail

{{
{WORKSPACE_TEMPLATE}
}} || {{
    error_message="$?"
    echo "❌ An error occurred: $error_message"
    {ERROR_NOTIFICATION_TEMPLATE}
    exit 1
}}
"""

def generate_terraform_vars_json(tf_vars):
    vars_dict = {var["name"]: f"${{{var['name']}}}" for var in tf_vars}
    return json.dumps(vars_dict, indent=2)

__all__ = ['tf_var', 'GIT_CLONE_COMMAND', 'COMMON_WORKSPACE_TEMPLATE', 'WORKSPACE_TEMPLATE_WITH_ERROR_HANDLING', 'ERROR_NOTIFICATION_TEMPLATE', 'generate_terraform_vars_json']
