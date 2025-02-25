from kubiya_sdk.tools import Tool, Volume
from kubiya_sdk.tools import Arg

GRYPE_ICON_URL = "https://raw.githubusercontent.com/anchore/grype/main/grype.png"
GRYPE_DOCKER_IMAGE = "anchore/grype:latest"

# Define volume for Grype database
GRYPE_DB_VOLUME = Volume(
    name="grype_db",
    path="/root/.cache/grype"
)

# Common environment variables and files
COMMON_ENV = [
    "GRYPE_DB_AUTO_UPDATE",
    "GRYPE_CHECK_FOR_APP_UPDATE",
    "GRYPE_DB_CACHE_DIR"
]

COMMON_FILES = []

# Define required secrets as simple names
COMMON_SECRETS = ["vendor_credentials"]

class GrypeTool(Tool):
    def __init__(self, name, description, content, args, long_running=False):
        enhanced_content = f"""
#!/bin/sh
set -e

# Install required tools
install_tools() {{
    echo "Installing required tools..."
    apk add --no-cache jq yq curl &>/dev/null || {{
        echo "Failed to install required tools"
        exit 1
    }}
}}

# Function to safely create directories
create_dir() {{
    local dir="$1"
    if [ ! -d "$dir" ]; then
        mkdir -p "$dir" || {{
            echo "Failed to create directory: $dir"
            exit 1
        }}
    fi
}}

# Function to setup Grype database directory
setup_grype_db() {{
    echo "Setting up Grype database directory..."
    create_dir "{GRYPE_DB_VOLUME.path}"
    
    # Ensure proper permissions
    chmod 755 "{GRYPE_DB_VOLUME.path}"
    
    # Initialize/update the database
    echo "Initializing/updating Grype database..."
    if ! grype db status &>/dev/null; then
        echo "Performing initial database download..."
        grype db update || {{
            echo "Failed to initialize Grype database"
            exit 1
        }}
    fi
}}

# Function to safely write files
write_file() {{
    local file="$1"
    local content="$2"
    local dir=$(dirname "$file")
    
    create_dir "$dir"
    echo "$content" > "$file" || {{
        echo "Failed to write to file: $file"
        exit 1
    }}
}}

# Function to validate vendor credentials
validate_vendor_credentials() {{
    if [ -z "$VENDOR_CREDENTIALS" ]; then
        echo "Warning: No vendor credentials provided"
        return 0
    fi

    # Validate JSON structure
    if ! echo "$VENDOR_CREDENTIALS" | jq . >/dev/null 2>&1; then
        echo "Error: Invalid JSON in vendor credentials"
        exit 1
    fi

    # Validate required fields for each provider if configured
    if echo "$VENDOR_CREDENTIALS" | jq -e '.registry' >/dev/null 2>&1; then
        if ! echo "$VENDOR_CREDENTIALS" | jq -e '.registry.username and .registry.password and .registry.url' >/dev/null 2>&1; then
            echo "Error: Registry credentials missing required fields (username, password, url)"
            exit 1
        fi
    fi

    if echo "$VENDOR_CREDENTIALS" | jq -e '.redhat' >/dev/null 2>&1; then
        if ! echo "$VENDOR_CREDENTIALS" | jq -e '.redhat.username and .redhat.password' >/dev/null 2>&1; then
            echo "Error: Red Hat credentials missing required fields (username, password)"
            exit 1
        fi
    fi

    if echo "$VENDOR_CREDENTIALS" | jq -e '.kubernetes' >/dev/null 2>&1; then
        if ! echo "$VENDOR_CREDENTIALS" | jq -e '.kubernetes.kubeconfig' >/dev/null 2>&1; then
            echo "Error: Kubernetes credentials missing required field (kubeconfig)"
            exit 1
        fi
    fi

    if echo "$VENDOR_CREDENTIALS" | jq -e '.aws' >/dev/null 2>&1; then
        if ! echo "$VENDOR_CREDENTIALS" | jq -e '.aws.access_key_id and .aws.secret_access_key and .aws.region' >/dev/null 2>&1; then
            echo "Error: AWS credentials missing required fields (access_key_id, secret_access_key, region)"
            exit 1
        fi
    fi

    if echo "$VENDOR_CREDENTIALS" | jq -e '.azure' >/dev/null 2>&1; then
        if ! echo "$VENDOR_CREDENTIALS" | jq -e '.azure.client_id and .azure.client_secret and .azure.tenant_id' >/dev/null 2>&1; then
            echo "Error: Azure credentials missing required fields (client_id, client_secret, tenant_id)"
            exit 1
        fi
    fi
}}

# Function to setup vendor credentials
setup_vendor_credentials() {{
    # Validate credentials first
    validate_vendor_credentials
    
    if [ -n "$VENDOR_CREDENTIALS" ]; then
        echo "Setting up vendor credentials..."
        
        # Setup Registry credentials
        if echo "$VENDOR_CREDENTIALS" | jq -e '.registry' >/dev/null 2>&1; then
            REGISTRY_USERNAME=$(echo "$VENDOR_CREDENTIALS" | jq -r '.registry.username')
            REGISTRY_PASSWORD=$(echo "$VENDOR_CREDENTIALS" | jq -r '.registry.password')
            REGISTRY_URL=$(echo "$VENDOR_CREDENTIALS" | jq -r '.registry.url')
            
            echo "Configuring registry authentication..."
            local config_dir="/root/.docker"
            local config_file="$config_dir/config.json"
            local auth=$(echo -n "$REGISTRY_USERNAME:$REGISTRY_PASSWORD" | base64)
            local config_content="{{\\"auths\\":{{\\"$REGISTRY_URL\\":{{\\"auth\\":\\"$auth\\"}}}}}}"
            write_file "$config_file" "$config_content"
        fi
        
        # Setup Red Hat credentials
        if echo "$VENDOR_CREDENTIALS" | jq -e '.redhat' >/dev/null 2>&1; then
            REDHAT_USERNAME=$(echo "$VENDOR_CREDENTIALS" | jq -r '.redhat.username')
            REDHAT_PASSWORD=$(echo "$VENDOR_CREDENTIALS" | jq -r '.redhat.password')
            
            echo "Configuring Red Hat authentication..."
            local config_dir="/etc/grype"
            local config_file="$config_dir/redhat.yaml"
            local config_content="credentials:
  username: $REDHAT_USERNAME
  password: $REDHAT_PASSWORD"
            write_file "$config_file" "$config_content"
        fi
        
        # Setup Kubernetes credentials
        if echo "$VENDOR_CREDENTIALS" | jq -e '.kubernetes.kubeconfig' >/dev/null 2>&1; then
            echo "Configuring Kubernetes credentials..."
            local kubeconfig_dir="/root/.kube"
            local kubeconfig_file="$kubeconfig_dir/config"
            echo "$VENDOR_CREDENTIALS" | jq -r '.kubernetes.kubeconfig' | base64 -d > "$kubeconfig_file"
        fi
        
        # Setup AWS credentials
        if echo "$VENDOR_CREDENTIALS" | jq -e '.aws' >/dev/null 2>&1; then
            echo "Configuring AWS credentials..."
            local aws_dir="/root/.aws"
            local aws_config_file="$aws_dir/config"
            local aws_creds_file="$aws_dir/credentials"
            
            create_dir "$aws_dir"
            echo "[default]
region = $(echo "$VENDOR_CREDENTIALS" | jq -r '.aws.region')" > "$aws_config_file"
            
            echo "[default]
aws_access_key_id = $(echo "$VENDOR_CREDENTIALS" | jq -r '.aws.access_key_id')
aws_secret_access_key = $(echo "$VENDOR_CREDENTIALS" | jq -r '.aws.secret_access_key')" > "$aws_creds_file"
        fi
        
        # Setup Azure credentials
        if echo "$VENDOR_CREDENTIALS" | jq -e '.azure' >/dev/null 2>&1; then
            echo "Configuring Azure credentials..."
            export AZURE_CLIENT_ID=$(echo "$VENDOR_CREDENTIALS" | jq -r '.azure.client_id')
            export AZURE_CLIENT_SECRET=$(echo "$VENDOR_CREDENTIALS" | jq -r '.azure.client_secret')
            export AZURE_TENANT_ID=$(echo "$VENDOR_CREDENTIALS" | jq -r '.azure.tenant_id')
        fi
    fi
}}

# Function to verify Grype installation
verify_grype() {{
    if ! command -v grype &>/dev/null; then
        echo "Grype not found in PATH"
        exit 1
    fi
    
    # Verify Grype version and database
    grype version || {{
        echo "Failed to verify Grype version"
        exit 1
    }}
}}

# Main execution
echo "Initializing Grype environment..."
install_tools
setup_grype_db
verify_grype
setup_vendor_credentials

echo "Starting Grype operation..."
{content}
"""
        
        super().__init__(
            name=name,
            description=description,
            docker_image=GRYPE_DOCKER_IMAGE,
            icon_url=GRYPE_ICON_URL,
            content=enhanced_content,
            args=args,
            env=COMMON_ENV,
            files=COMMON_FILES,
            secrets=COMMON_SECRETS,
            volumes=[GRYPE_DB_VOLUME],  # Add the volume to the tool
            long_running=long_running
        ) 