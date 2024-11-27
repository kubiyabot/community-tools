from kubiya_sdk.tools import Arg, Volume
from .base import GitHubCliTool
from kubiya_sdk.tools.registry import tool_registry
import os

class VolumeRepoTool(GitHubCliTool):
    def __init__(self, name, description, content, args, long_running=False):
        enhanced_content = f"""
#!/bin/sh
set -e

# Ensure we're working within the volume directory
cd /var/git_data

# Create email-specific directory if it doesn't exist
WORK_DIR="/var/git_data/$KUBIYA_USER_EMAIL"
mkdir -p "$WORK_DIR"
cd "$WORK_DIR"

if ! command -v jq >/dev/null 2>&1; then
    # Silently install jq
    apk add --quiet jq >/dev/null 2>&1
fi

check_and_set_org() {{
    if [ -n "$org" ]; then
        echo "Using organization: $org"
    else
        orgs=$(gh api user/orgs --jq '.[].login')
        org_count=$(echo "$orgs" | wc -l)
        if [ "$org_count" -eq 0 ]; then
            echo "You are not part of any organization."
        elif [ "$org_count" -eq 1 ]; then
            org=$orgs
            echo "You are part of one organization: $org. Using this organization."
        else
            echo "You are part of the following organizations:"
            echo "$orgs"
            echo "Please specify the organization in your command if needed."
        fi
    fi
}}

get_repo_context() {{
    if [ -z "$repo" ]; then
        if [ -n "$org" ]; then
            echo "No repository specified. Here are your 10 most recently updated repositories in the $org organization:"
            gh repo list $org --limit 10 --json nameWithOwner --jq '.[].nameWithOwner'
        else
            echo "No repository specified. Here are your 10 most recently updated repositories:"
            gh repo list --limit 10 --json nameWithOwner --jq '.[].nameWithOwner'
        fi
        echo "NOTE: This is not a complete list of your repositories."
        echo "Please specify a repository name in your command."
        exit 1
    else
        if [[ "$repo" != *"/"* ]]; then
            if [ -n "$org" ]; then
                repo="${{org}}/${{repo}}"
            else
                current_user=$(gh api user --jq '.login')
                repo="${{current_user}}/${{repo}}"
            fi
        fi
        echo "Using repository: $repo"
    fi
}}

check_and_set_org
get_repo_context

{content}
"""
        updated_args = [arg for arg in args if arg.name not in ["org", "repo"]]
        updated_args.extend([
            Arg(name="org", type="str", description="GitHub organization name. If you're a member of only one org, it will be used automatically.", required=False),
            Arg(name="repo", type="str", description="Repository name. If org is provided or auto-detected, you can just specify the repo name. Otherwise, use the format 'owner/repo'.", required=False)
        ])

        super().__init__(
            name=name,
            description=description,
            content=enhanced_content,
            args=updated_args,
            long_running=long_running,
            with_volumes=[Volume(name="git_data", path="/var/git_data")]
        )

# Repository Management Tools
list_repos = VolumeRepoTool(
    name="github_list_cloned_repos",
    description="List all cloned repositories with their status",
    content="""
echo "Cloned Repositories:"
for dir in "$WORK_DIR"/*/ ; do
    if [ -d "$dir/.git" ]; then
        cd "$dir"
        echo "\n📁 $(basename "$dir")"
        echo "Branch: $(git branch --show-current)"
        git status --short
        echo "Last commit: $(git log -1 --pretty=format:'%h - %s (%cr)')"
    fi
done
""",
    args=[],
)

clean_repos = VolumeRepoTool(
    name="github_clean_cloned_repos_vol",
    description="Clean up cloned repositories",
    content="""
if [ -n "$repo_name" ]; then
    if [ -d "$WORK_DIR/$repo_name" ]; then
        rm -rf "$WORK_DIR/$repo_name"
        echo "Removed repository: $repo_name"
    else
        echo "Repository not found: $repo_name"
        exit 1
    fi
else
    rm -rf "$WORK_DIR"/*
    echo "Cleaned all repositories"
fi
""",
    args=[
        Arg(name="repo_name", type="str", description="Specific repository to remove (optional)", required=False),
    ],
)

# Git Operations Tools
git_status = VolumeRepoTool(
    name="github_git_status_cloned_repo",
    description="Show git status of a repository",
    content="""
if [ ! -d "$WORK_DIR/$repo_name" ]; then
    echo "Repository not found: $repo_name"
    exit 1
fi

cd "$WORK_DIR/$repo_name"
git status
""",
    args=[
        Arg(name="repo_name", type="str", description="Name of the repository", required=True),
    ],
)

git_commit_file = VolumeRepoTool(
    name="github_git_commit_file_cloned_repo",
    description="Commit specific file(s) in a repository",
    content="""
if [ ! -d "$WORK_DIR/$repo_name" ]; then
    echo "Repository not found: $repo_name"
    exit 1
fi

cd "$WORK_DIR/$repo_name"
git config user.email "$KUBIYA_USER_EMAIL"
git config user.name "$KUBIYA_USER_EMAIL"

git add $files
git commit -m "$message"
echo "Changes committed successfully"
""",
    args=[
        Arg(name="repo_name", type="str", description="Name of the repository", required=True),
        Arg(name="files", type="str", description="Space-separated list of files to commit", required=True),
        Arg(name="message", type="str", description="Commit message", required=True),
    ],
)

git_commit_all = VolumeRepoTool(
    name="github_git_commit_all",
    description="Commit all changes in a repository",
    content="""
if [ ! -d "$WORK_DIR/$repo_name" ]; then
    echo "Repository not found: $repo_name"
    exit 1
fi

cd "$WORK_DIR/$repo_name"
git config user.email "$KUBIYA_USER_EMAIL"
git config user.name "$KUBIYA_USER_EMAIL"

git add -A
git commit -m "$message"
echo "All changes committed successfully"
""",
    args=[
        Arg(name="repo_name", type="str", description="Name of the repository", required=True),
        Arg(name="message", type="str", description="Commit message", required=True),
    ],
)

git_push = VolumeRepoTool(
    name="github_git_push",
    description="Push changes to remote repository",
    content="""
if [ ! -d "$WORK_DIR/$repo_name" ]; then
    echo "Repository not found: $repo_name"
    exit 1
fi

cd "$WORK_DIR/$repo_name"
git push origin $([[ -n "$branch" ]] && echo "$branch" || echo "HEAD") $([[ "$force" == "true" ]] && echo "--force")
echo "Changes pushed successfully"
""",
    args=[
        Arg(name="repo_name", type="str", description="Name of the repository", required=True),
        Arg(name="branch", type="str", description="Branch to push to (defaults to current branch)", required=False),
        Arg(name="force", type="bool", description="Force push changes", required=False),
    ],
)

git_branch = VolumeRepoTool(
    name="github_git_branch_cloned_repo",
    description="Create or switch branches",
    content="""
if [ ! -d "$WORK_DIR/$repo_name" ]; then
    echo "Repository not found: $repo_name"
    exit 1
fi

cd "$WORK_DIR/$repo_name"

if [ -n "$new_branch" ]; then
    git checkout -b "$new_branch"
    echo "Created and switched to new branch: $new_branch"
elif [ -n "$switch_to" ]; then
    git checkout "$switch_to"
    echo "Switched to branch: $switch_to"
else
    echo "Current branches:"
    git branch
fi
""",
    args=[
        Arg(name="repo_name", type="str", description="Name of the repository", required=True),
        Arg(name="new_branch", type="str", description="Name of new branch to create", required=False),
        Arg(name="switch_to", type="str", description="Existing branch to switch to", required=False),
    ],
)

git_log = VolumeRepoTool(
    name="github_git_log",
    description="Show commit history",
    content="""
if [ ! -d "$WORK_DIR/$repo_name" ]; then
    echo "Repository not found: $repo_name"
    exit 1
fi

cd "$WORK_DIR/$repo_name"
git log --pretty=format:"%h - %s (%cr) <%an>" --graph $([[ -n "$limit" ]] && echo "-n $limit")
""",
    args=[
        Arg(name="repo_name", type="str", description="Name of the repository", required=True),
        Arg(name="limit", type="int", description="Limit number of commits to show", required=False),
    ],
)

git_diff = VolumeRepoTool(
    name="github_git_diff_cloned_repo",
    description="Show changes in repository",
    content="""
if [ ! -d "$WORK_DIR/$repo_name" ]; then
    echo "Repository not found: $repo_name"
    exit 1
fi

cd "$WORK_DIR/$repo_name"
if [ -n "$file" ]; then
    git diff "$file"
else
    git diff
fi
""",
    args=[
        Arg(name="repo_name", type="str", description="Name of the repository", required=True),
        Arg(name="file", type="str", description="Specific file to show diff for", required=False),
    ],
)

# Register all tools
tools = [
    list_repos,
    clean_repos,
    git_status,
    git_commit_file,
    git_commit_all,
    git_push,
    git_branch,
    git_log,
    git_diff,
]

for tool in tools:
    tool_registry.register("github", tool)

__all__ = [
    "VolumeRepoTool"
]