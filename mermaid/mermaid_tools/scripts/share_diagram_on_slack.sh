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

# Debug: Show the diagram content being processed
echo "📝 Processing diagram with content length: $(echo "$diagram_content" | wc -c) characters"
echo "🎯 Output will be saved as: $OUTPUT_FILE"

echo "🖌️ Generating diagram..."
if ! echo "$diagram_content" | mmdc -p /puppeteer-config.json --input - --output "$OUTPUT_FILE"; then
    echo "❌ Failed to generate diagram. Error occurred during mmdc execution."
    exit 1
fi

# Verify the file was created
if [ ! -f "$OUTPUT_FILE" ]; then
    echo "❌ Output file was not created!"
    exit 1
fi

echo "✅ Diagram generated successfully! File size: $(ls -lh "$OUTPUT_FILE" | awk '{print $5}')"

echo "📤 Uploading to Slack channel: $slack_destination"
if ! slack file upload "$OUTPUT_FILE" --channels "$slack_destination" --title "$comment"; then
    echo "❌ Failed to upload to Slack"
    exit 1
fi

echo "✨ Success! Diagram has been generated and shared on Slack"