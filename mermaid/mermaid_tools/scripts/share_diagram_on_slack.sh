#!/bin/sh
set -e

echo "🎨 Generating diagram..."

# Check required arguments
if [ -z "${diagram_content:-}" ] || [ -z "${slack_destination:-}" ]; then
    echo "❌ Error: Both diagram_content and slack_destination are required."
    exit 1
fi

# Set defaults
comment="${comment:-Here is the diagram.}"
output_format="${output_format:-png}"
OUTPUT_FILE="/data/diagram.${output_format}"

# Generate diagram
echo "$diagram_content" | mmdc -p /puppeteer-config.json --input - --output "$OUTPUT_FILE"

# Share on Slack
slack file upload "$OUTPUT_FILE" --channels "$slack_destination" --title "$comment"

echo "✨ Done!"