# Schedule Task Tool

## Description

The `schedule_task` tool allows you to schedule a task using the Kubiya API. This Python script sets up tasks to be executed at a specified future time based on a provided delay.

## Usage

### Arguments

- **execution_delay**: The delay before the task is executed (e.g., `5h` for 5 hours, `30m` for 30 minutes). This argument is required.

### Environment Variables

The tool requires several environment variables to be set for authentication and task details:

- **KUBIYA_API_KEY**: The API key for Kubiya (fetched from Kubiya secret).
- **USER_ID**: The user ID (fetched from Kubiya secret).
- **SLACK_CHANNEL_ID**: The Slack channel ID (fetched from Kubiya secret).
- **TEAM_ID**: The team ID (fetched from Kubiya secret).
- **USER_EMAIL**: The user's email address (fetched from Kubiya secret).
- **ORGANIZATION**: The organization name (fetched from Kubiya secret).
- **AGENT**: The selected agent (fetched from Kubiya secret).

### Dependencies

The tool requires the following Python packages:

- `requests==2.25.1`
- `pytimeparse==1.1.8`

### Example

To use the `schedule_task` tool, ensure that the necessary environment variables are set and provide the `execution_delay` argument. For example, to schedule a task to be executed in 5 hours:

```sh
schedule_task --execution_delay 5h
```

## License
This tool is licensed under the MIT License. See the LICENSE file for more details.
