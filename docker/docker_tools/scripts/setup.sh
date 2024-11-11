#!/bin/bash

source /tmp/scripts/utils.sh

# Install basic dependencies silently
setup_dependencies() {
    log "🔧" "Installing basic dependencies..."
    apt-get update -qq && apt-get install -qq -y git curl jq > /dev/null 2>&1
    setup_python_env
}

# Setup Git credentials and SSH if needed
setup_git() {
    if [ -n "${GITHUB_TOKEN}" ] || [ -n "${GIT_SSH_KEY}" ]; then
        log "🔑" "Setting up Git credentials..."
        
        # Configure Git
        git config --global credential.helper store
        
        # Setup GitHub token if available
        if [ -n "${GITHUB_TOKEN}" ]; then
            echo "https://x-access-token:${GITHUB_TOKEN}@github.com" > ~/.git-credentials
            git config --global credential.helper store
            log "🔒" "Configured GitHub token authentication"
        fi
        
        # Setup SSH key if available
        if [ -n "${GIT_SSH_KEY}" ]; then
            mkdir -p ~/.ssh
            echo "${GIT_SSH_KEY}" > ~/.ssh/id_rsa
            chmod 600 ~/.ssh/id_rsa
            ssh-keyscan github.com >> ~/.ssh/known_hosts 2>/dev/null
            log "🔑" "Configured SSH key authentication"
        fi
    fi
}

# Setup Docker authentication if credentials are available
setup_docker() {
    if [ -n "${DOCKER_USERNAME}" ] && [ -n "${DOCKER_PASSWORD}" ]; then
        log "🐳" "Setting up Docker authentication..."
        echo "${DOCKER_PASSWORD}" | docker login --username "${DOCKER_USERNAME}" --password-stdin >/dev/null 2>&1
    fi
}

# Set default environment variables if not already set
setup_env() {
    log "⚙️" "Configuring environment variables..."
    
    # Set Docker defaults only if not already set
    : ${DOCKER_HOST:=unix:///var/run/docker.sock}
    : ${DOCKER_BUILDKIT:=1}
    : ${DOCKER_CLI_EXPERIMENTAL:=enabled}
    : ${DOCKER_DEFAULT_PLATFORM:=linux/amd64}
    
    export DOCKER_HOST DOCKER_BUILDKIT DOCKER_CLI_EXPERIMENTAL DOCKER_DEFAULT_PLATFORM
}

# Main setup
main_setup() {
    setup_env
    setup_dependencies
    setup_git
    setup_docker
}

# Run setup
main_setup 