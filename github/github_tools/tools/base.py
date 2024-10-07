from kubiya_sdk.tools import Tool, FileSpec
from kubiya_sdk.tools import Arg

GITHUB_ICON_URL = "https://cdn-icons-png.flaticon.com/256/25/25231.png"

class GitHubCliTool(Tool):
    def __init__(self, name, description, content, args, long_running=False):
        # Prepend jq check and organization check to the content
        enhanced_content = """
        #!/bin/bash
        set -e

        # Check if jq is installed, if not, install it
        if ! command -v jq &> /dev/null; then
            echo "jq is not installed. Installing jq..."
            apt-get update && apt-get install -y jq
        fi

        # Function to check if user is part of an organization
        check_org() {
            orgs=$(gh api user/orgs --jq '.[].login')
            if [ -z "$orgs" ]; then
                echo "You are not part of any organization."
            else
                echo "You are part of the following organizations:"
                echo "$orgs"
                echo "Please specify the organization in your command if needed."
            fi
        }

        # Function to get repository context
        get_repo_context() {
            if [ -z "$repo" ]; then
                echo "No repository specified. Here are your 10 most recently updated repositories:"
                gh repo list --limit 10
                echo "NOTE: This is not a complete list of your repositories."
                echo "To work with repositories, you can use the following tools:"
                echo "  - 'github_repo_list' to see more of your repositories"
                echo "  - 'github_repo_view' to view details of a specific repository"
                echo "  - 'github_repo_search' to search for repositories"
                echo "  - 'github_repo_create' to create a new repository"
                echo "Please specify a repository in your command or use one of the above tools to find or create the repository you need."
                exit 1
            fi
        }

        # Check organization membership
        check_org

        # Get repository context if not provided
        get_repo_context

        # Original command content
        {0}
        """.format(content)

        # Add org and repo arguments if not present
        has_org_arg = any(arg.name == "org" for arg in args)
        has_repo_arg = any(arg.name == "repo" for arg in args)

        if not has_org_arg:
            args.append(Arg(name="org", type="str", description="GitHub organization name. Example: 'myorg'", required=False))
        if not has_repo_arg:
            args.append(Arg(name="repo", type="str", description="Repository name in 'owner/repo' format. Example: 'myorg/myrepo'", required=False))

        super().__init__(
            name=name,
            description=description,
            icon_url=GITHUB_ICON_URL,
            type="docker",
            image="ghcr.io/cli/cli:latest",
            content=enhanced_content,
            args=args,
            env=["GITHUB_TOKEN"],
            files=[
                FileSpec(source="~/.config/gh/config.yml", destination="/root/.config/gh/config.yml"),
                FileSpec(source="~/.config/gh/hosts.yml", destination="/root/.config/gh/hosts.yml"),
            ],
            long_running=long_running
        )
