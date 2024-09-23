import json

from jinja2 import Template


# Function to create Terraform variable dictionaries
def tf_var(name, description, required=False, default=None):
    return {
        "name": name,
        "description": description,
        "required": required,
        "default": default,
    }


# Git clone command for fetching Terraform configurations
GIT_CLONE_COMMAND = 'git clone -b "$BRANCH" "https://$PAT@github.com/$GIT_ORG/$GIT_REPO.git" "iac_workspace"'


def generate_terraform_vars_json(tf_vars):
    vars_dict = {}
    for var in tf_vars:
        name = var["name"]
        default = var.get("default")

        if default is not None:
            value = default
        else:
            value = "{{ ." + f"{name}" + " }}"
        # Try to parse the default value as JSON
        try:
            # This will handle booleans, numbers, lists, and nulls
            value_parsed = json.loads(value)
        except (json.JSONDecodeError, TypeError):
            # If it's not valid JSON, treat it as a string
            value_parsed = value

        vars_dict[name] = value_parsed

    return json.dumps(vars_dict, indent=2)


COMMON_WORKSPACE_TEMPLATE_JINJA = """
#!/bin/bash
export TERRAFORM_NO_COLOR=true
export TF_INPUT=false

set -eo pipefail  # Removing 'u' to prevent unset variable errors

DATABRICKS_ICON_URL="{!DATABRICKS_ICON_URL!}"

apk add jq curl git --quiet

send_slack_message() {
    local status=$1
    local message=$2
    local color=$3

    # Escape special characters in the message for JSON
    escaped_message=$(echo "$message" | jq -R -s '.')

    SLACK_MESSAGE_CONTENT=$(cat <<EOF
{
    "channel": "$SLACK_CHANNEL_ID",
    "thread_ts": "$SLACK_THREAD_TS",
    "attachments": [
        {
            "color": "$color",
            "blocks": [
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "image",
                            "image_url": "{!DATABRICKS_ICON_URL!}",
                            "alt_text": "Databricks Logo"
                        },
                        {
                            "type": "mrkdwn",
                            "text": "🔧 Databricks workspace provisioning $status"
                        }
                    ]
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": $escaped_message
                    }
                }
            ]
        }
    ]
}
EOF
    )

    curl -X POST "https://slack.com/api/chat.postMessage" \\
        -H "Authorization: Bearer $SLACK_API_TOKEN" \\
        -H "Content-Type: application/json; charset=utf-8" \\
        --data "$SLACK_MESSAGE_CONTENT"
}

report_failure() {
    local step=$1
    local error_message=$2
    local error_output=$3

    # Truncate the error output to the last 2000 characters
    truncated_error_output=$(echo "$error_output" | tail -c 2000)

    # Prepare the message with error output
    error_message_full=$(printf "❌ Error during %s: %s\n*Last part of the error log:*\n\\`\\`\\`%s\\`\\`\\`" "$step" "$error_message" "$truncated_error_output")

    send_slack_message "failed" "$error_message_full" "danger"

    # Print the error to the console for visibility
    echo -e "$error_message_full"

    exit 1
}

echo -e "🛠️ Setting up Databricks workspace on {!CLOUD_PROVIDER!}..."
{!GIT_CLONE_COMMAND!} || report_failure "Git clone" "Failed to clone repository" "$(git clone 2>&1)"

cd iac_workspace/{!TERRAFORM_MODULE_PATH!} || report_failure "Directory change" "Failed to change to Terraform module directory" "$(cd iac_workspace/{!TERRAFORM_MODULE_PATH!} 2>&1)"

echo -e "🔍 Validating input parameters..."
check_var() {
    var_name="$1"
    var_value="$(printenv "$var_name")"
    if [ -z "$var_value" ]; then
        report_failure "Input validation" "${var_name} is not set" ""
    fi
}
# Check required variables
{!CHECK_REQUIRED_VARS!}

echo -e "✅ All required parameters are set."
echo -e "🚀 Initializing Terraform..."
if ! {!TERRAFORM_INIT_COMMAND!} 2>&1 | tee /tmp/terraform_init.log; then
    error_output=$(cat /tmp/terraform_init.log)
    report_failure "Terraform init" "Failed to initialize Terraform" "$error_output"
fi

echo -e "🏗️ Applying Terraform configuration..."
cat << EOF > terraform.tfvars.json
{!TERRAFORM_VARS_JSON!}
EOF

if ! terraform apply -auto-approve -var-file=terraform.tfvars.json 2>&1 | tee /tmp/terraform_apply.log; then
    error_output=$(cat /tmp/terraform_apply.log)
    report_failure "Terraform apply" "Failed to apply Terraform configuration" "$error_output"
fi

echo "📊 Capturing Terraform output..."
tf_output=$(terraform output -json) || report_failure "Terraform output" "Failed to capture Terraform output" "$(terraform output -json 2>&1)"
workspace_url=$(echo "$tf_output" | jq -r '.databricks_host.value // empty')
workspace_url="${workspace_url:-"{!FALLBACK_WORKSPACE_URL!}"}"

echo "🔍 Getting backend config..."
backend_config=$(terraform show -json | jq -r '.values.backend_config // empty') || report_failure "Backend config" "Failed to get backend configuration" "$(terraform show -json 2>&1)"

echo "💬 Preparing Slack message..."
success_message=$(jq -n \
    --arg org "${GIT_ORG}" \
    --arg repo "{!GIT_REPO!}" \
    --arg backend_type "{!BACKEND_TYPE!}" \
    --arg backend_config "$backend_config!" \
    --arg import_command "{!IMPORT_COMMAND!}" \
    '{
        "text": "🎉 Your *Databricks workspace* was successfully provisioned using *Terraform*, following *Infrastructure as Code (IAC)* best practices.\n\n👉 *Module Source code*: <https://github.com/\($org)/\($repo)|Explore the module>\n\n*To import the state locally, follow these steps:*\n1. Configure your Terraform backend:\n```\nterraform {\n  backend \"\($backend_type)\" {\n    \($backend_config)\n  }\n}\n```\n2. Run the import command:\n```\n\($import_command)\n```"
    }' | jq -r '.text')

send_slack_message "succeeded" "$success_message" "good" || report_failure "Slack notification" "Failed to send success message to Slack" ""

echo -e "✅ Databricks workspace setup complete!"
"""

# Common workspace creation template
COMMON_WORKSPACE_TEMPLATE = Template(
    COMMON_WORKSPACE_TEMPLATE_JINJA,
    variable_start_string="{!",
    variable_end_string="!}",
)

# COMMON_WORKSPACE_TEMPLATE = """
# #!/bin/bash
# export TERRAFORM_NO_COLOR=true
# export TF_INPUT=false
# set -eo pipefail  # Removing 'u' to prevent unset variable errors

# DATABRICKS_ICON_URL="{DATABRICKS_ICON_URL}"

# apk add jq curl git --quiet

# send_slack_message() {
#     local status=$1
#     local message=$2
#     local color=$3

#     # Escape special characters in the message for JSON
#     escaped_message=$(echo "$message" | jq -R -s '.')

#     SLACK_MESSAGE_CONTENT=$(cat <<EOF
# {
#     "channel": "$SLACK_CHANNEL_ID",
#     "thread_ts": "$SLACK_THREAD_TS",
#     "attachments": [
#         {
#             "color": "$color",
#             "blocks": [
#                 {
#                     "type": "context",
#                     "elements": [
#                         {
#                             "type": "image",
#                             "image_url": "{DATABRICKS_ICON_URL}",
#                             "alt_text": "Databricks Logo"
#                         },
#                         {
#                             "type": "mrkdwn",
#                             "text": "🔧 Databricks workspace provisioning $status"
#                         }
#                     ]
#                 },
#                 {
#                     "type": "section",
#                     "text": {
#                         "type": "mrkdwn",
#                         "text": $escaped_message
#                     }
#                 }
#             ]
#         }
#     ]
# }
# EOF
#     )

#     curl -X POST "https://slack.com/api/chat.postMessage" \\
#         -H "Authorization: Bearer $SLACK_API_TOKEN" \\
#         -H "Content-Type: application/json; charset=utf-8" \\
#         --data "$SLACK_MESSAGE_CONTENT"
# }}

# report_failure() {
#     local step=$1
#     local error_message=$2
#     local error_output=$3

#     # Truncate the error output to the last 2000 characters
#     truncated_error_output=$(echo "$error_output" | tail -c 2000)

#     # Prepare the message with error output
#     error_message_full=$(printf "❌ Error during %s: %s\n*Last part of the error log:*\n\\`\\`\\`%s\\`\\`\\`" "$step" "$error_message" "$truncated_error_output")

#     send_slack_message "failed" "$error_message_full" "danger"

#     # Print the error to the console for visibility
#     echo -e "$error_message_full"

#     exit 1
# }

# echo -e "🛠️ Setting up Databricks workspace on {CLOUD_PROVIDER}..."
# {GIT_CLONE_COMMAND} || report_failure "Git clone" "Failed to clone repository" "$(git clone 2>&1)"

# cd iac_workspace/{TERRAFORM_MODULE_PATH} || report_failure "Directory change" "Failed to change to Terraform module directory" "$(cd iac_workspace/{TERRAFORM_MODULE_PATH} 2>&1)"

# echo -e "🔍 Validating input parameters..."
# check_var() {
#     var_name="$1"
#     var_value="$(printenv "$var_name")"
#     if [ -z "$var_value" ]; then
#         report_failure "Input validation" "${{var_name}} is not set" ""
#     fi
# }
# # Check required variables
# {CHECK_REQUIRED_VARS}

# echo -e "✅ All required parameters are set."
# echo -e "🚀 Initializing Terraform..."
# if ! terraform init {TERRAFORM_INIT_COMMAND} 2>&1 | tee /tmp/terraform_init.log; then
#     error_output=$(cat /tmp/terraform_init.log)
#     report_failure "Terraform init" "Failed to initialize Terraform" "$error_output"
# fi

# echo -e "🏗️ Applying Terraform configuration..."
# cat << EOF > terraform.tfvars.json
# {TERRAFORM_VARS_JSON}
# EOF

# if ! terraform apply -auto-approve -var-file=terraform.tfvars.json 2>&1 | tee /tmp/terraform_apply.log; then
#     error_output=$(cat /tmp/terraform_apply.log)
#     report_failure "Terraform apply" "Failed to apply Terraform configuration" "$error_output"
# fi

# echo "📊 Capturing Terraform output..."
# tf_output=$(terraform output -json) || report_failure "Terraform output" "Failed to capture Terraform output" "$(terraform output -json 2>&1)"
# workspace_url=$(echo "$tf_output" | jq -r '.databricks_host.value // empty')
# workspace_url="${{workspace_url:-"{FALLBACK_WORKSPACE_URL}"}}"

# echo "🔍 Getting backend config..."
# backend_config=$(terraform show -json | jq -r '.values.backend_config // empty') || report_failure "Backend config" "Failed to get backend configuration" "$(terraform show -json 2>&1)"

# echo "💬 Preparing Slack message..."
# success_message=$(jq -n \
#     --arg org "${{GIT_ORG}}" \
#     --arg repo "{GIT_REPO}" \
#     --arg backend_type "{BACKEND_TYPE}" \
#     --arg backend_config "$backend_config" \
#     --arg import_command "{IMPORT_COMMAND}" \
#     '{
#         "text": "🎉 Your *Databricks workspace* was successfully provisioned using *Terraform*, following *Infrastructure as Code (IAC)* best practices.\n\n👉 *Module Source code*: <https://github.com/\\($org)/\\($repo)|Explore the module>\n\n*To import the state locally, follow these steps:*\n1. Configure your Terraform backend:\n```\nterraform {\n  backend \"\\($backend_type)\" {\n    \\($backend_config)\n  }\n}\n```\n2. Run the import command:\n```\n\\($import_command)\n```"
#     }' | jq -r '.text')

# send_slack_message "succeeded" "$success_message" "good" || report_failure "Slack notification" "Failed to send success message to Slack" ""

# echo -e "✅ Databricks workspace setup complete!"
# """

# Workspace template with error handling
WORKSPACE_TEMPLATE_WITH_ERROR_HANDLING = """{WORKSPACE_TEMPLATE}"""
