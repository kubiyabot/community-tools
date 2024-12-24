#!/bin/bash
set -e

# Extract command type and provider from arguments
COMMAND_TYPE=$1
PROVIDER=$2
shift 2

# Function to install terraformer
install_terraformer() {
    echo "Installing terraformer..."
    export PROVIDER=all
    LATEST_VERSION=$(curl -s https://api.github.com/repos/GoogleCloudPlatform/terraformer/releases/latest | grep tag_name | cut -d '"' -f 4)
    curl -LO "https://github.com/GoogleCloudPlatform/terraformer/releases/download/${LATEST_VERSION}/terraformer-${PROVIDER}-linux-amd64"
    chmod +x terraformer-${PROVIDER}-linux-amd64
    mv terraformer-${PROVIDER}-linux-amd64 /usr/local/bin/terraformer
    echo "Terraformer installed successfully"
}

# Function to validate environment variables
validate_env_vars() {
    local provider=$1
    case $provider in
        aws)
            [[ -z "$AWS_ACCESS_KEY_ID" ]] && echo "Missing AWS_ACCESS_KEY_ID" && exit 1
            [[ -z "$AWS_SECRET_ACCESS_KEY" ]] && echo "Missing AWS_SECRET_ACCESS_KEY" && exit 1
            [[ -z "$AWS_REGION" ]] && echo "Missing AWS_REGION" && exit 1
            ;;
        gcp)
            [[ -z "$GOOGLE_CREDENTIALS" ]] && echo "Missing GOOGLE_CREDENTIALS" && exit 1
            [[ -z "$GOOGLE_PROJECT" ]] && echo "Missing GOOGLE_PROJECT" && exit 1
            ;;
        azure)
            [[ -z "$AZURE_SUBSCRIPTION_ID" ]] && echo "Missing AZURE_SUBSCRIPTION_ID" && exit 1
            [[ -z "$AZURE_CLIENT_ID" ]] && echo "Missing AZURE_CLIENT_ID" && exit 1
            [[ -z "$AZURE_CLIENT_SECRET" ]] && echo "Missing AZURE_CLIENT_SECRET" && exit 1
            [[ -z "$AZURE_TENANT_ID" ]] && echo "Missing AZURE_TENANT_ID" && exit 1
            ;;
        *)
            echo "Unsupported provider: $provider"
            exit 1
            ;;
    esac
}

# Install terraformer if not already installed
if ! command -v terraformer &> /dev/null; then
    install_terraformer
fi

# Validate environment variables
validate_env_vars "$PROVIDER"

case $COMMAND_TYPE in
    import)
        # Parse import arguments
        RESOURCE_TYPE=$1
        RESOURCE_ID=$2
        OUTPUT_DIR=${3:-terraform_imported}

        # Validate required arguments
        [[ -z "$RESOURCE_TYPE" ]] && echo "resource_type is required for import" && exit 1
        [[ -z "$RESOURCE_ID" ]] && echo "resource_id is required for import" && exit 1

        # Create output directory
        mkdir -p "$OUTPUT_DIR"

        # Run import command
        terraformer import "$PROVIDER" \
            --resources "$RESOURCE_TYPE" \
            --filter "$RESOURCE_ID" \
            --path-output "$OUTPUT_DIR"
        ;;

    scan)
        # Parse scan arguments
        RESOURCE_TYPES=${1:-all}
        OUTPUT_FORMAT=${2:-hcl}

        # Run scan command
        terraformer scan "$PROVIDER" \
            --resources "$RESOURCE_TYPES" \
            --output "$OUTPUT_FORMAT"
        ;;

    *)
        echo "Unknown command type: $COMMAND_TYPE"
        exit 1
        ;;
esac 