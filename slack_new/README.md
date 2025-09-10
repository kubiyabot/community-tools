# Slack Tools

Kubiya Slack integration tools with dual token support for enhanced channel discovery and messaging.

## Features

- **Dual Token System**: Uses Kubiya integration token for messaging and high-tier app token for channel discovery
- **Channel Discovery**: Find channel IDs by name with comprehensive search across channel types
- **Message Sending**: Send messages to channels using channel IDs
- **Rate Limiting**: Built-in rate limiting for API requests

## Tools

### 1. slack_find_channel_by_name
Find Slack channel ID by name using high-tier token. Searches across public, private channels and DMs.

**Arguments:**
- `channel_name` (required): Channel name to search for (with or without # prefix)

### 2. slack_send_message  
Send message to Slack channel using channel ID. Use slack_find_channel_by_name first to get the channel ID.

**Arguments:**
- `channel` (required): Channel ID (use slack_find_channel_by_name to get ID first)
- `message` (required): Message text to send (supports Slack markdown)
- `thread_ts` (optional): Thread timestamp for replies

## Environment Variables

- `KUBIYA_API_TOKEN`: Required for accessing Kubiya APIs
- The tools automatically fetch Slack tokens from:
  - Kubiya integration API: `api/v1/integration/slack/token/1`
  - Kubiya secrets API: `api/v1/secret/get_secret_value/slack_app_token`

## Usage Flow

1. **Find Channel ID**: Use `slack_find_channel_by_name` tool to get the channel ID
2. **Send Message**: Use the returned channel ID with `slack_send_message` tool

**Example Workflow:**
```bash
# Step 1: Find channel ID
slack_find_channel_by_name --channel_name "general"
# Output: Channel ID: C1234567890

# Step 2: Send message using channel ID  
slack_send_message --channel "C1234567890" --message "Hello from Kubiya!"
```

## Integration with Kubiya

These tools are designed to work with the Kubiya platform and use the Kubiya SDK for tool registration and execution. The tools automatically:

- Fetch Slack tokens from Kubiya APIs
- Handle rate limiting and error cases  
- Provide clear guidance on proper usage
- Support threaded messages and various channel types

## Docker Usage

```bash
# Build image
docker build -t slack-tools .

# The tools are executed through the Kubiya platform
# and don't require direct Docker execution
```