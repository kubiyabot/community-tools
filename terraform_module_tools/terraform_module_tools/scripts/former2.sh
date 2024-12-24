#!/bin/bash
set -e

# Function to handle errors
handle_error() {
    echo "Error: $1" >&2
    exit 1
}

# Check if Former2 is installed
if ! command -v former2 &> /dev/null; then
    handle_error "Former2 CLI is not installed. Please install it with: npm install -g former2"
fi

# Parse arguments
COMMAND="$1"
PROVIDER="$2"
shift 2

case "$COMMAND" in
    scan)
        RESOURCE_TYPES="$1"
        OUTPUT_FORMAT="$2"
        
        # Run Former2 scan
        former2 generate \
            --output-terraform - \
            --services "$RESOURCE_TYPES" \
            --region "$AWS_REGION" \
            --profile "$AWS_PROFILE" || handle_error "Former2 scan failed"
        ;;
    import)
        RESOURCE_TYPE="$1"
        RESOURCE_ID="$2"
        OUTPUT_DIR="$3"
        
        # Run Former2 import
        former2 generate \
            --output-terraform - \
            --services "$RESOURCE_TYPE" \
            --search-filter "$RESOURCE_ID" \
            --region "$AWS_REGION" \
            --profile "$AWS_PROFILE" || handle_error "Former2 import failed"
        ;;
    *)
        handle_error "Unknown command: $COMMAND"
        ;;
esac 