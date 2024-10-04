from kubiya_sdk.tools import Tool
from kubiya_sdk.tools.registry import tool_registry

class PagerDutyDockerTool(Tool):
    def __init__(self, name, description, content, args, env):
        self.name = name
        self.description = description
        self.content = content
        self.args = args
        self.env = env

    def register(self, category):
        tool_registry.register(category, self)

    @staticmethod
    def get_common_env():
        return [
            "PD_API_KEY",
            "SLACK_API_TOKEN",
            "TARGET_SLACK_CHANNEL",
            "FSAPI_PROD",
            "AZURE_TENANT_ID",
            "AZURE_CLIENT_ID",
            "AZURE_CLIENT_SECRET",
            "KUBIYA_USER_EMAIL",
            "TOOLS_GH_TOKEN",
            "PAGERDUTY_SERVICE_ID",
            "PAGERDUTY_ESCALATION_POLICY_ID",
            "REPO_BRANCH",
            "GIT_ORG",
            "REPO_NAME",
            "SOURCE_CODE_DIR",
            "REPO_DIR",
        ]

    @staticmethod
    def get_common_script():
        return """
#!/bin/sh

# Install necessary packages
apk add --no-cache git curl python3 py3-pip jq

# Fetch variables from environment
SOURCE_CODE_DIR="${SOURCE_CODE_DIR:-/src}"
REPO_DIR="${REPO_DIR:-$REPO_NAME}"

# Validate required environment variables
if [ -z "$GIT_ORG" ] || [ -z "$REPO_NAME" ] || [ -z "$TOOLS_GH_TOKEN" ]; then
    echo "GIT_ORG, REPO_NAME, and TOOLS_GH_TOKEN environment variables must be set."
    exit 1
fi

# Clone repository if not already cloned
if [ ! -d "$REPO_DIR" ]; then
    git clone -b "$REPO_BRANCH" https://"$TOOLS_GH_TOKEN"@github.com/"$GIT_ORG"/"$REPO_NAME".git "$REPO_DIR"
fi

cd "${REPO_DIR}/${SOURCE_CODE_DIR}"

# Install Python requirements
if [ -f "requirements.txt" ]; then
    pip3 install --no-cache-dir -r requirements.txt
fi

# Execute the script with provided arguments
export PYTHONPATH="${PYTHONPATH}:/${REPO_DIR}/${SOURCE_CODE_DIR}"

# Function to get access token from Azure
get_access_token() {
    response=$(curl -s -X POST "https://login.microsoftonline.com/$AZURE_TENANT_ID/oauth2/v2.0/token" \
        -d "client_id=$AZURE_CLIENT_ID" \
        -d "scope=https://graph.microsoft.com/.default" \
        -d "client_secret=$AZURE_CLIENT_SECRET" \
        -d "grant_type=client_credentials")
    echo $(echo $response | jq -r '.access_token')
}

# Function to get on-call engineer from PagerDuty
get_oncall_engineer() {
    response=$(curl -s -X GET "https://api.pagerduty.com/oncalls?escalation_policy_ids[]=$PAGERDUTY_ESCALATION_POLICY_ID" \
        -H "Authorization: Token token=$PD_API_KEY" \
        -H "Accept: application/vnd.pagerduty+json;version=2")
    echo $(echo $response | jq -r '.oncalls[0].user.summary')
}

# Function to create PagerDuty incident
create_pd_incident() {
    response=$(curl -s -X POST "https://api.pagerduty.com/incidents" \
        -H "Authorization: Token token=$PD_API_KEY" \
        -H "Content-Type: application/json" \
        -d "{
            \"incident\": {
                \"type\": \"incident\",
                \"title\": \"Major Incident via Kubiya - $description\",
                \"service\": {\"id\": \"$PAGERDUTY_SERVICE_ID\", \"type\": \"service_reference\"},
                \"escalation_policy\": {\"id\": \"$PAGERDUTY_ESCALATION_POLICY_ID\", \"type\": \"escalation_policy_reference\"},
                \"body\": {\"type\": \"incident_body\", \"details\": \"$description\"}
            }
        }")
    echo $(echo $response | jq -r '.incident.id')
}

# Function to create FreshService ticket
create_ticket() {
    response=$(curl -s -X POST "https://aenetworks.freshservice.com/api/v2/tickets" \
        -H "Content-Type: application/json" \
        -u "$FSAPI_PROD:X" \
        -d "{
            \"description\": \"$description<br><strong>Incident Commander:</strong> $incident_commander<br><strong>Detection Method:</strong> Detection Method<br><strong>Business Impact:</strong> $business_impact<br><strong>Ticket Link:</strong>PagerDuty Incident\",
            \"subject\": \"MAJOR INCIDENT pagerduty-kubiya-page-oncall-service - Major Incident via Kubiya\",
            \"email\": \"$KUBIYA_USER_EMAIL\",
            \"priority\": 1,
            \"status\": 2,
            \"source\": 8,
            \"category\": \"DevOps\",
            \"sub_category\": \"Pageout\",
            \"tags\": [\"PDID_$incident_id\"]
        }")
    echo $(echo $response | jq -r '.ticket.id')
}

# Function to create Microsoft Teams meeting
create_meeting() {
    start_time=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    end_time=$(date -u -d "+1 hour" +"%Y-%m-%dT%H:%M:%SZ")
    response=$(curl -s -X POST "https://graph.microsoft.com/v1.0/users/d69debf1-af1f-493f-8837-35747e55ea0f/onlineMeetings" \
        -H "Authorization: Bearer $access_token" \
        -H "Content-Type: application/json" \
        -d "{
            \"startDateTime\": \"$start_time\",
            \"endDateTime\": \"$end_time\"
        }")
    echo $(echo $response | jq -r '.joinUrl')
}

# Function to send Slack message
send_slack_message() {
    curl -s -X POST "https://slack.com/api/chat.postMessage" \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $SLACK_API_TOKEN" \
        -d "{
            \"channel\": \"$TARGET_SLACK_CHANNEL\",
            \"text\": \"$1\"
        }"
}

# Main script execution
description="$1"
business_impact="$2"

if [ -z "$description" ] || [ -z "$business_impact" ]; then
    echo "Usage: trigger_major_incident_communication.sh <description> <business_impact>"
    exit 1
fi

access_token=$(get_access_token)
incident_commander=$(get_oncall_engineer)
incident_id=$(create_pd_incident)
ticket_id=$(create_ticket)
meeting_link=$(create_meeting)

message="
************** SEV 1 ****************
Incident Commander: $incident_commander
Description: $description
Business Impact: $business_impact
Bridge Link: $meeting_link
PagerDuty Incident URL: https://aetnd.pagerduty.com/incidents/$incident_id
FS Ticket URL: https://aenetworks.freshservice.com/a/tickets/$ticket_id
Reported by: $KUBIYA_USER_EMAIL
We will keep everyone posted on this channel as we assess the issue further.
"

send_slack_message "$message"

echo "Incident created successfully with ID: $incident_id"
"""
