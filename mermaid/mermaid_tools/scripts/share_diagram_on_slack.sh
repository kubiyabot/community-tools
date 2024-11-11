#!/bin/sh
set -e

echo "🎨 Starting diagram generation process..."

# Check required arguments and token
if [ -z "${diagram_content:-}" ] || [ -z "${slack_destination:-}" ]; then
    echo "❌ Error: Both diagram_content and slack_destination are required."
    exit 1
fi

if [ -z "${SLACK_API_TOKEN:-}" ]; then
    echo "❌ Error: SLACK_API_TOKEN environment variable is required."
    exit 1
fi

# Set defaults
comment="${comment:-Here is the diagram.}"
output_format="${output_format:-png}"
OUTPUT_FILE="/data/diagram.${output_format}"

# Handle optional theme and background color
theme_arg=""
if [ -n "${theme:-}" ]; then
    theme_arg="--theme ${theme}"
fi

bg_arg=""
if [ -n "${background_color:-}" ]; then
    bg_arg="--backgroundColor ${background_color}"
fi

echo "📝 Diagram content:"
echo "$diagram_content"

echo "🖌️ Generating diagram..."
# Using mmdc from its installed location in the Docker image
if ! echo "$diagram_content" | /home/mermaidcli/node_modules/.bin/mmdc -p /puppeteer-config.json \
    --input - \
    --output "$OUTPUT_FILE" \
    $theme_arg \
    $bg_arg; then
    echo "❌ Failed to generate diagram"
    exit 1
fi

# Verify the file was created
if [ ! -f "$OUTPUT_FILE" ]; then
    echo "❌ Output file was not created!"
    exit 1
fi

echo "✅ Diagram generated successfully! File size: $(ls -lh "$OUTPUT_FILE" | awk '{print $5}')"

echo "📤 Uploading to Slack: $slack_destination"

# Prepare the curl command for file upload
CURL_CMD="curl -s -F file=@$OUTPUT_FILE"
CURL_CMD="$CURL_CMD -F 'initial_comment=$comment'"

# Handle different Slack destinations
if [ -n "${SLACK_CHANNEL_ID:-}" ]; then
    # We're in a specific channel context
    CURL_CMD="$CURL_CMD -F channels=$SLACK_CHANNEL_ID"
    if [ -n "${SLACK_THREAD_TS:-}" ]; then
        # We're in a thread
        CURL_CMD="$CURL_CMD -F thread_ts=$SLACK_THREAD_TS"
    fi
elif [[ "$slack_destination" == "#"* ]]; then
    # It's a channel
    CURL_CMD="$CURL_CMD -F channels=${slack_destination#"#"}"
elif [[ "$slack_destination" == "@"* ]]; then
    # It's a direct message
    CURL_CMD="$CURL_CMD -F channels=${slack_destination#"@"}"
else
    echo "❌ Invalid slack_destination format. Use #channel or @user"
    exit 1
fi

# Execute the upload
if ! $CURL_CMD \
    -H "Authorization: Bearer $SLACK_API_TOKEN" \
    "https://slack.com/api/files.upload" | grep -q '"ok":true'; then
    echo "❌ Failed to upload to Slack"
    exit 1
fi

echo "✨ Success! Diagram has been generated and shared on Slack"