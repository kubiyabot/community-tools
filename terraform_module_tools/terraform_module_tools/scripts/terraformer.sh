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
            [[ -z "$AWS_ACCESS_KEY_ID" ]] && echo "AWS_ACCESS_KEY_ID is required" && exit 1
            [[ -z "$AWS_SECRET_ACCESS_KEY" ]] && echo "AWS_SECRET_ACCESS_KEY is required" && exit 1
            [[ -z "$AWS_REGION" ]] && echo "AWS_REGION is required" && exit 1
            ;;
        gcp)
            [[ -z "$GOOGLE_CREDENTIALS" ]] && echo "GOOGLE_CREDENTIALS is required" && exit 1
            [[ -z "$GOOGLE_PROJECT" ]] && echo "GOOGLE_PROJECT is required" && exit 1
            ;;
        azure)
            [[ -z "$AZURE_SUBSCRIPTION_ID" ]] && echo "AZURE_SUBSCRIPTION_ID is required" && exit 1
            [[ -z "$AZURE_CLIENT_ID" ]] && echo "AZURE_CLIENT_ID is required" && exit 1
            [[ -z "$AZURE_CLIENT_SECRET" ]] && echo "AZURE_CLIENT_SECRET is required" && exit 1
            [[ -z "$AZURE_TENANT_ID" ]] && echo "AZURE_TENANT_ID is required" && exit 1
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

# Execute command based on type
case $COMMAND_TYPE in
    import)
        RESOURCE_TYPE=${1:-vpc}
        RESOURCE_ID=${2:-}
        OUTPUT_DIR=${3:-terraform_imported}

        # Run import command
        terraformer import "$PROVIDER" \
            --resources "$RESOURCE_TYPE" \
            --filter "$RESOURCE_ID" \
            --path-pattern "$OUTPUT_DIR"
        ;;

    scan)
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