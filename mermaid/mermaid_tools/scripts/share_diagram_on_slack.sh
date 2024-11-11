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

# Initialize upload parameters with proper filename and title
upload_params="-F file=@$OUTPUT_FILE;filename=diagram.${output_format} -F initial_comment=$comment -F title=Mermaid Diagram -H Authorization: Bearer $SLACK_API_TOKEN"

# Handle different Slack destinations
if [ -n "${SLACK_CHANNEL_ID:-}" ]; then
    # We're in a specific channel context
    upload_params="$upload_params -F channels=$SLACK_CHANNEL_ID"
    if [ -n "${SLACK_THREAD_TS:-}" ]; then
        # We're in a thread
        upload_params="$upload_params -F thread_ts=$SLACK_THREAD_TS"
    fi
elif [ "$slack_destination" = "#"* ]; then
    # It's a channel
    channel="${slack_destination#"#"}"
    upload_params="$upload_params -F channels=$channel"
elif [ "$slack_destination" = "@"* ]; then
    # It's a direct message - need to get user ID first
    username="${slack_destination#"@"}"
    user_response=$(curl -s -H "Authorization: Bearer $SLACK_API_TOKEN" \
        "https://slack.com/api/users.lookupByEmail?email=$username" || \
        curl -s -H "Authorization: Bearer $SLACK_API_TOKEN" \
        "https://slack.com/api/users.list" | jq -r ".members[] | select(.name==\"$username\").id")
    
    if [ -z "$user_response" ]; then
        echo "❌ Could not find user: $username"
        exit 1
    fi
    upload_params="$upload_params -F channels=$user_response"
else
    echo "❌ Invalid slack_destination format. Use #channel or @user"
    exit 1
fi

# Execute the upload with proper error handling
response=$(curl -s $upload_params "https://slack.com/api/files.upload")
ok=$(echo "$response" | jq -r '.ok')
error=$(echo "$response" | jq -r '.error // empty')

if [ "$ok" != "true" ]; then
    echo "❌ Failed to upload to Slack: ${error:-Unknown error}"
    echo "Full response: $response"
    exit 1
fi

echo "✨ Success! Diagram has been generated and shared on Slack"