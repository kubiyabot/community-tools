# Community Tools Repository

Welcome to the **Kubiya AI Community Tools** repository!
This repository is a collection of various tools contributed by the community to help streamline and automate workflows.
Each tool in this repository is designed to be easily configurable and extendable to fit different use cases.

## Repository Structure

Each tool in this repository is defined with a set of common fields to ensure consistency and ease of use.
Below is a brief overview of these fields:

### Common Fields

- **name**: The name of the tool.
- **description**: A brief description of what the tool does.
- **type**: The type of the tool (e.g., bash, python, docker).
- **alias**: A short alias to easily reference the tool.
- **content**: The script or command that the tool runs.
- **content_url**: URL to the content if hosted externally.
- **args**: Arguments that the tool accepts.
- **env**: Environment variables required by the tool.
- **dependencies**: Dependencies required by the tool.
- **dependencies_url**: URL to the dependencies if hosted externally.
- **openapi**: OpenAPI specification for the tool.
- **files**: Files to be used with the tool.
- **services**: Services required by the tool.
- **git_repo**: Git repository to be used with the tool.
- **volumes**: Volumes that the tool mounts.
- **icon_url**: URL to the icon for the tool.
- **image**: Docker image to be used by the tool.
- **long_running**: Indicates if the tool is long-running.
- **on_start**: Script to run on start.
- **on_complete**: Script to run on completion.

