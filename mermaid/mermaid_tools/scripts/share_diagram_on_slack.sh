#!/bin/sh
set -e

echo "🎨 Preparing to generate diagram..."

# Check required arguments
if [ -z "${diagram_content:-}" ] || [ -z "${slack_destination:-}" ]; then
    echo "❌ Error: Both diagram_content and slack_destination are required."
    exit 1
fi

# Set defaults if not provided
comment="${comment:-Here is the diagram.}"
output_format="${output_format:-png}"

# Create temporary workspace for output only
TEMP_DIR=$(mktemp -d)
OUTPUT_FILE="$TEMP_DIR/diagram_output.${output_format}"

# Set theme and background options
THEME_OPTION=""
BACKGROUND_OPTION=""
[ -n "${theme:-}" ] && THEME_OPTION="-t $theme"
[ -n "${background_color:-}" ] && BACKGROUND_OPTION="-b $background_color"

# Render the diagram using stdin
echo "🎯 Rendering diagram..."
if ! echo "$diagram_content" | mmdc --input - --output "$OUTPUT_FILE" -f "$output_format" $THEME_OPTION $BACKGROUND_OPTION; then
    echo "❌ Failed to render diagram. Please check your diagram syntax."
    rm -rf "$TEMP_DIR"
    exit 1
fi

# Upload to Slack
echo "📤 Sharing to Slack..."
if ! slack file upload "$OUTPUT_FILE" --channels "$slack_destination" --title "$comment"; then
    echo "❌ Failed to upload to Slack. Please check your Slack token and destination."
    rm -rf "$TEMP_DIR"
    exit 1
fi

rm -rf "$TEMP_DIR"
echo "✨ Diagram shared successfully!"