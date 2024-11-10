#!/bin/bash

# exit on error
set -e

# Check required arguments
if [ -z "${diagram_content:-}" ]; then
    echo "❌ Error: 'diagram_content' must be provided."
    exit 1
fi

if [ -z "${slack_destination:-}" ]; then
    echo "❌ Error: 'slack_destination' must be provided."
    exit 1
fi

# Set defaults if not provided
comment="${comment:-Here is the diagram.}"
output_format="${output_format:-png}"

# Create a temporary directory
TEMP_DIR=$(mktemp -d)
INPUT_FILE="$TEMP_DIR/diagram.mmd"
OUTPUT_FILE="$TEMP_DIR/diagram_output.${output_format}"

# Write the diagram content to a file
echo "$diagram_content" > "$INPUT_FILE"

# Set theme and background options
THEME_OPTION=""
if [ -n "${theme:-}" ]; then
    THEME_OPTION="-t $theme"
fi

BACKGROUND_OPTION=""
if [ -n "${background_color:-}" ]; then
    BACKGROUND_OPTION="-b $background_color"
fi

# Render the diagram using mermaid-cli
if ! mmdc -i "$INPUT_FILE" -o "$OUTPUT_FILE" -f "$output_format" $THEME_OPTION $BACKGROUND_OPTION; then
    echo "❌ Error: Failed to render diagram."
    rm -rf "$TEMP_DIR"
    exit 1
fi

# Upload the diagram to Slack using slack-cli
if ! slack file upload "$OUTPUT_FILE" --channels "$slack_destination" --title "$comment"; then
    echo "❌ Error: Failed to upload the diagram to Slack."
    rm -rf "$TEMP_DIR"
    exit 1
fi

echo "✅ Diagram shared on Slack successfully!"

# Clean up temporary files
rm -rf "$TEMP_DIR"