#!/bin/sh
set -e

echo "🎨 Starting diagram generation process..."

# Check required arguments
if [ -z "${diagram_content:-}" ] || [ -z "${slack_destination:-}" ]; then
    echo "❌ Error: Both diagram_content and slack_destination are required."
    exit 1
fi

echo "📋 Validating inputs..."
# Set defaults
comment="${comment:-Here is the diagram.}"
output_format="${output_format:-png}"
OUTPUT_FILE="/data/diagram.${output_format}"

echo "🖌️ Generating diagram..."
echo "$diagram_content" | mmdc -p /puppeteer-config.json --input - --output "$OUTPUT_FILE"

echo "📤 Uploading to Slack channel: $slack_destination"
slack file upload "$OUTPUT_FILE" --channels "$slack_destination" --title "$comment"

echo "✨ Done! Diagram has been generated and shared."