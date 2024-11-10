from ..base import MermaidTool
from kubiya_sdk.tools import Arg

share_diagram_on_slack_tool = MermaidTool(
    name="share_diagram_on_slack",
    description="Renders a Mermaid diagram from raw input and shares it on Slack. You can specify the Slack destination using @ for direct messages or # for channels.",
    content="""
#!/bin/bash
set -euo pipefail

# Function to display engaging messages
function print_with_delay() {
    local message="$1"
    echo "$message"
    sleep 1
}

print_with_delay "📥 Preparing to share diagram on Slack..."

# Check if diagram_content is provided
if [ -z "${diagram_content:-}" ]; then
    echo "❌ Error: 'diagram_content' must be provided."
    exit 1
fi

# Validate diagram_content is not empty
if [ -z "$diagram_content" ]; then
    echo "❌ Error: 'diagram_content' is empty."
    exit 1
fi

# Check if Slack API token is provided
if [ -z "${SLACK_API_TOKEN:-}" ]; then
    echo "❌ Error: 'SLACK_API_TOKEN' must be set."
    exit 1
fi

# Set default values if not provided
CHANNEL="${slack_destination:-}"
COMMENT="${comment:-Here is the diagram.}"

if [ -z "$CHANNEL" ]; then
    echo "❌ Error: 'slack_destination' must be provided (e.g., '@username' or '#channelname')."
    exit 1
fi

# Create a temporary input file
INPUT_FILE=$(mktemp /tmp/diagram.XXXXXX.mmd)
echo "$diagram_content" > "$INPUT_FILE"

# Set output file
OUTPUT_FILE="diagram_output.${output_format:-png}"

# Set theme and background options
THEME_OPTION=""
if [ -n "${theme:-}" ]; then
    THEME_OPTION="-t $theme"
fi

BACKGROUND_OPTION=""
if [ -n "${background_color:-}" ]; then
    BACKGROUND_OPTION="-b $background_color"
fi

print_with_delay "🎨 Rendering the diagram..."

# Run mermaid-cli command to render the diagram
if ! mmdc -i "$INPUT_FILE" -o "$OUTPUT_FILE" -f "${output_format:-png}" $THEME_OPTION $BACKGROUND_OPTION; then
    echo "❌ Error: Failed to render the diagram."
    rm "$INPUT_FILE"
    exit 1
fi

print_with_delay "✅ Diagram rendered successfully!"

# Share on Slack
print_with_delay "📤 Uploading diagram to Slack..."
export SLACK_CLI_TOKEN="$SLACK_API_TOKEN"

# Determine Slack destination type
if [[ "$CHANNEL" == @* ]]; then
    DESTINATION_TYPE="--dest"
    DESTINATION="${CHANNEL#@}"
elif [[ "$CHANNEL" == \#* ]]; then
    DESTINATION_TYPE="--channel"
    DESTINATION="${CHANNEL#\#}"
else
    echo "❌ Error: 'slack_destination' must start with '@' for direct messages or '#' for channels."
    rm "$INPUT_FILE" "$OUTPUT_FILE"
    exit 1
fi

if ! slack file upload "$OUTPUT_FILE" "$DESTINATION_TYPE" "$DESTINATION" --comment "$COMMENT"; then
    echo "❌ Error: Failed to upload the diagram to Slack."
    rm "$INPUT_FILE" "$OUTPUT_FILE"
    exit 1
fi

print_with_delay "✅ Diagram shared on Slack successfully!"

# Clean up temporary files
rm "$INPUT_FILE" "$OUTPUT_FILE"
""",
    args=[
        Arg(name="diagram_content", type="str", description="Mermaid diagram content as a string.", required=True),
        Arg(name="slack_destination", type="str", description="Slack destination to send the diagram. Use '@username' for direct messages or '#channelname' for channels.", required=True),
        Arg(name="comment", type="str", description="Comment to include with the uploaded diagram. Defaults to 'Here is the diagram.'", required=False),
        Arg(name="output_format", type="str", description="Output format for the diagram (svg, png, pdf). Defaults to 'png'.", required=False),
        Arg(name="theme", type="str", description="Theme for rendering the diagram ('default', 'dark', 'forest', 'neutral'). Optional.", required=False),
        Arg(name="background_color", type="str", description="Background color or 'transparent'. Optional.", required=False),
    ],
)