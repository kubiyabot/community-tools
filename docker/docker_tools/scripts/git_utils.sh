#!/bin/bash

source /tmp/scripts/utils.sh

# Function to perform lightweight clone
git_clone_lightweight() {
    local repo_url="$1"
    local branch="${2:-main}"
    local target_dir="$3"
    local depth="${4:-1}"

    if [ -z "$target_dir" ]; then
        target_dir=$(mktemp -d)
    fi

    log "📦" "Cloning $repo_url ($branch) into $target_dir..."
    
    # Perform shallow clone with specific branch
    git clone --depth=$depth --single-branch --branch "$branch" "$repo_url" "$target_dir" > /dev/null 2>&1
    
    echo "$target_dir"
}

# Function to find Dockerfile in repository
find_dockerfile() {
    local repo_dir="$1"
    local dockerfile_path="${2:-Dockerfile}"
    
    log "🔍" "Searching for Dockerfile in $repo_dir..."
    
    # Check if specific path exists
    if [ -f "$repo_dir/$dockerfile_path" ]; then
        log "✅" "Found Dockerfile at specified path"
        echo "$repo_dir/$dockerfile_path"
        return 0
    fi
    
    # Search for Dockerfile recursively
    local found_dockerfile=$(find "$repo_dir" -name "Dockerfile" -type f | head -n 1)
    
    if [ -n "$found_dockerfile" ]; then
        log "✅" "Found Dockerfile at $found_dockerfile"
        echo "$found_dockerfile"
        return 0
    fi
    
    log "❌" "No Dockerfile found"
    return 1
}

# Function to get repository metadata
get_repo_metadata() {
    local repo_dir="$1"
    
    cd "$repo_dir"
    
    log "📊" "Collecting repository metadata..."
    
    # Get repository information
    local remote_url=$(git config --get remote.origin.url)
    local current_branch=$(git rev-parse --abbrev-ref HEAD)
    local latest_commit=$(git rev-parse HEAD)
    local latest_tag=$(git describe --tags --abbrev=0 2>/dev/null || echo "no tags")
    
    # Return as JSON
    echo "{
        \"remote_url\": \"$remote_url\",
        \"branch\": \"$current_branch\",
        \"commit\": \"$latest_commit\",
        \"latest_tag\": \"$latest_tag\"
    }"
} 