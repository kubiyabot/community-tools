# Slack Tools for Kubiya SDK

This package provides a set of tools, designed to assist with various Slack workspace management and communication tasks.

## Available Actions
### 1. Send a Message
Send a custom message to a specified Slack channel.
**Parameters:**
- channel: The Slack channel name (with or without # prefix) or ID.
- text: The message text. Markdown is supported.
### 2. Delete a Message
Delete a specific message from a Slack channel.
**Parameters:**
- channel: The Slack channel containing the message.
- ts: Timestamp of the message to be deleted.
### 3. Update a Message
Update the content of an existing message in a Slack channel.
**Parameters:**
- channel: The Slack channel containing the message.
- ts: Timestamp of the message to be updated.
- text: The new message text.
### 4. Add a Reaction
Add a reaction (emoji) to a specific message.
**Parameters:**
- channel: The Slack channel containing the message.
- timestamp: Timestamp of the message.
- name: Name of the emoji to react with.
### 5. Remove a Reaction
Remove a reaction (emoji) from a specific message.
**Parameters:**
- channel: The Slack channel containing the message.
- timestamp: Timestamp of the message.
- name: Name of the emoji to remove.
### 6. Upload a File
Upload a file to specified Slack channels.
**Parameters:**
- channels: Comma-separated list of channel IDs to share the file to.
- content: Content of the file.
- filename: Name of the file.
- initial_comment: Initial comment for the file.
### 7. Get User Info
Get detailed information about a specific Slack user.
**Parameters:**
- user: The ID of the user to get info for.
### 8. Get Channel History
Retrieve the message history of a specific Slack channel.
**Parameters:**
- channel: The ID of the channel to fetch history from.
- limit: Number of messages to return (default is 10).