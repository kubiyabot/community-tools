# shared_templates.py

import json

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

# Function to generate Terraform variables in JSON format
def generate_terraform_vars_json(tf_vars):
    json_lines = ['{']
    for i, var in enumerate(tf_vars):
        name = var['name']
        default = var.get('default')
        if default is not None:
            value = default
        else:
            value = "${" + name + "}"
        # Determine the correct representation based on the value type
        if isinstance(value, str):
            if value.lower() in ["true", "false"]:
                # Handle booleans
                json_line = f'  "{name}": {value.lower()}'
            elif value.startswith('[') and value.endswith(']'):
                # Handle lists
                json_line = f'  "{name}": {value}'
            else:
                # Handle strings with variable expansion
                json_line = f'  "{name}": "{value}"'
        else:
            # Handle numbers and other types
            json_line = f'  "{name}": {value}'
        if i < len(tf_vars) - 1:
            json_line += ','
        json_lines.append(json_line)
    json_lines.append('}')
    return '\n'.join(json_lines)

# Common workspace creation template
COMMON_WORKSPACE_TEMPLATE = """
#!/bin/bash
export TERRAFORM_NO_COLOR=true
export TF_INPUT=false
set -euo pipefail

DATABRICKS_ICON_URL="{DATABRICKS_ICON_URL}"

apk add jq curl git --quiet

echo -e "🛠️ Setting up Databricks workspace on {CLOUD_PROVIDER}..."
{GIT_CLONE_COMMAND}

cd iac_workspace/{TERRAFORM_MODULE_PATH}

echo -e "🔍 Validating input parameters..."
check_var() {{
    var_name="$1"
    if [ -z "${{!var_name:-}}" ]]; then
        echo "❌ Error: ${{var_name}} is not set."
        exit 1
    fi
}}
# Check required variables
{CHECK_REQUIRED_VARS}

echo -e "✅ All required parameters are set."
echo -e "🚀 Initializing Terraform..."
{TERRAFORM_INIT_COMMAND}

echo -e "🏗️ Applying Terraform configuration..."
cat << EOF > terraform.tfvars.json
{TERRAFORM_VARS_JSON}
EOF

terraform apply -auto-approve -var-file=terraform.tfvars.json

echo "📊 Capturing Terraform output..."
tf_output=$(terraform output -json)
workspace_url=$(echo "$tf_output" | jq -r '.databricks_host.value // empty')
workspace_url="${{workspace_url:-"{FALLBACK_WORKSPACE_URL}"}}"

echo "🔍 Getting backend config..."
backend_config=$(terraform show -json | jq -r '.values.backend_config // empty')

echo "💬 Preparing Slack message..."
SLACK_MESSAGE_CONTENT=$(cat <<EOF
{...}  # Existing Slack message content
EOF
)

echo -e "📤 Sending Slack message..."
curl -X POST "https://slack.com/api/chat.postMessage" \\
-H "Authorization: Bearer $SLACK_API_TOKEN" \\
-H "Content-Type: application/json" \\
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
                "text": "*Error Message:*\n\`\`\`$error_message\`\`\`"
            }}
        }}
    ]
}}
EOF
)

curl -X POST "https://slack.com/api/chat.postMessage" \\
-H "Authorization: Bearer $SLACK_API_TOKEN" \\
-H "Content-Type: application/json" \\
--data "$SLACK_ERROR_MESSAGE_CONTENT"
"""

# Workspace template with error handling
WORKSPACE_TEMPLATE_WITH_ERROR_HANDLING = """
{{
{WORKSPACE_TEMPLATE}
}} || {{

    error_message="$?"
    echo "❌ An error occurred: $error_message"
    {ERROR_NOTIFICATION_TEMPLATE}
    exit 1
}}
"""
