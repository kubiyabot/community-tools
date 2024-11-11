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

# Use default CSS file if no custom CSS provided
css_arg=""
if [ -n "${css_file:-}" ]; then
    css_arg="--cssFile ${css_file}"
else
    # Use our default CSS for SVG output
    if [ "$output_format" = "svg" ]; then
        css_arg="--cssFile /tmp/styles/default.css"
    fi
fi

echo "📝 Diagram content:"
echo "${diagram_content}"

echo "🖌️ Generating diagram..."
# Using mmdc from its installed location in the Docker image
if ! printf '%s' "${diagram_content}" | /home/mermaidcli/node_modules/.bin/mmdc -p /puppeteer-config.json \
    --input - \
    --output "${OUTPUT_FILE}" \
    ${theme_arg} \
    ${bg_arg} \
    ${css_arg}; then
    echo "❌ Failed to generate diagram"
    exit 1
fi

# Verify the file was created
if [ ! -f "${OUTPUT_FILE}" ]; then
    echo "❌ Output file was not created!"
    exit 1
fi

echo "✅ Diagram generated successfully! File size: $(ls -lh "${OUTPUT_FILE}" | awk '{print $5}')"

echo "📤 Uploading to Slack: ${slack_destination}"

# Handle different Slack destinations
channel=""
if [ -n "${SLACK_CHANNEL_ID:-}" ]; then
    # We're in a specific channel context
    channel="${SLACK_CHANNEL_ID}"
    channel_comment="${comment}"
    
    # Prepare thread upload command if needed
    if [ -n "${SLACK_THREAD_TS:-}" ]; then
        channel_comment="${comment} (Also shared in thread)"
        (
            echo "📎 Uploading to thread..."
            thread_response=$(curl -s \
                -F "file=@${OUTPUT_FILE}" \
                -F "filename=diagram.${output_format}" \
                -F "channels=${channel}" \
                -F "thread_ts=${SLACK_THREAD_TS}" \
                -F "initial_comment=${comment}" \
                -H "Authorization: Bearer ${SLACK_API_TOKEN}" \
                "https://slack.com/api/files.upload")
            
            thread_ok=$(printf '%s' "${thread_response}" | jq -r '.ok')
            if [ "${thread_ok}" != "true" ]; then
                echo "⚠️ Warning: Failed to upload to thread"
            else
                echo "✅ Uploaded to thread successfully"
            fi
        ) &
        thread_pid=$!
    fi
elif [ "${slack_destination}" = "#"* ]; then
    # It's a channel
    channel="${slack_destination#"#"}"
    channel_comment="${comment}"
elif [ "${slack_destination}" = "@"* ]; then
    # It's a direct message - need to get user ID first
    username="${slack_destination#"@"}"
    user_response=$(curl -s -H "Authorization: Bearer ${SLACK_API_TOKEN}" \
        "https://slack.com/api/users.lookupByEmail?email=${username}" || \
        curl -s -H "Authorization: Bearer ${SLACK_API_TOKEN}" \
        "https://slack.com/api/users.list" | jq -r ".members[] | select(.name==\"${username}\").id")
    
    if [ -z "${user_response}" ]; then
        echo "❌ Could not find user: ${username}"
        exit 1
    fi
    channel="${user_response}"
    channel_comment="${comment}"
else
    echo "❌ Invalid slack_destination format. Use #channel or @user"
    exit 1
fi

# Execute the channel upload in parallel
(
    echo "📎 Uploading to channel..."
    response=$(curl -s \
        -F "file=@${OUTPUT_FILE}" \
        -F "filename=diagram.${output_format}" \
        -F "channels=${channel}" \
        -F "initial_comment=${channel_comment}" \
        -H "Authorization: Bearer ${SLACK_API_TOKEN}" \
        "https://slack.com/api/files.upload")

    ok=$(printf '%s' "${response}" | jq -r '.ok')
    error=$(printf '%s' "${response}" | jq -r '.error // empty')

    if [ "${ok}" != "true" ]; then
        echo "❌ Failed to upload to Slack: ${error:-Unknown error}"
        echo "Full response: ${response}"
        exit 1
    fi
    echo "✅ Uploaded to channel successfully"
) &
channel_pid=$!

# Wait for all uploads to complete
if [ -n "${thread_pid:-}" ]; then
    wait ${thread_pid}
fi
wait ${channel_pid}

echo "✨ Success! Diagram has been generated and shared on Slack"