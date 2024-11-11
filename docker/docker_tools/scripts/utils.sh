#!/bin/bash

# Common utility functions for all scripts

# Function to log with emoji and timestamp
log() {
    local emoji="$1"
    local message="$2"
    echo "$(date '+%Y-%m-%d %H:%M:%S') $emoji $message"
}

# Function to format JSON output
format_output() {
    while IFS= read -r line; do
        if echo "$line" | jq . >/dev/null 2>&1; then
            # Parse JSON and add formatting
            local status=$(echo "$line" | jq -r '.status')
            local message=$(echo "$line" | jq -r '.message')
            
            case "$status" in
                "starting")
                    log "🚀" "$message"
                    ;;
                "progress")
                    log "⏳" "$message"
                    ;;
                "success")
                    log "✅" "$message"
                    # Print additional details
                    echo "$line" | jq -r '
                        if has("image_id") then "   Image ID: " + .image_id else empty end,
                        if has("registry_url") then "   Registry URL: " + .registry_url else empty end
                    ' | grep -v null
                    ;;
                "error")
                    log "❌" "Error: $message"
                    if echo "$line" | jq -e 'has("details")' >/dev/null; then
                        echo "   Details: $(echo "$line" | jq -r '.details')"
                    fi
                    ;;
            esac
        else
            echo "$line"
        fi
    done
}

# Function to validate JSON input
validate_json() {
    local input="$1"
    local name="$2"
    if ! echo "$input" | jq . >/dev/null 2>&1; then
        log "❌" "Invalid $name JSON format"
        return 1
    fi
    return 0
}

# Function to setup Python environment
setup_python_env() {
    log "🔧" "Setting up Python environment..."
    pip install -q dagger-io > /dev/null 2>&1
} 