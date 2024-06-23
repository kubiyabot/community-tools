# ConfigCat CLI Tool

## Description

The `configcat_cli` tool allows you to run ConfigCat CLI commands using a Docker image from Docker Hub. This tool leverages the ConfigCat CLI to manage feature flags and configurations.

## Usage

### Arguments

- **command**: The ConfigCat CLI command to run (e.g., `settings list --config-id=<your_config_id>`). This argument is required.

### Environment Variables

The tool requires several environment variables to be set for authentication and task execution:

- **CONFIGCAT_API_USER**: The ConfigCat API user (fetched from Kubiya secret).
- **CONFIGCAT_API_PASS**: The ConfigCat API password (fetched from Kubiya secret).
- **CONFIGCAT_TOKEN**: The ConfigCat token (fetched from Kubiya secret).

## License
This tool is licensed under the MIT License. See the LICENSE file for more details.
