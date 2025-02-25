from kubiya_sdk.tools.models import Arg, Tool, Volume

GRYPE_ICON_URL = "https://raw.githubusercontent.com/anchore/grype/main/grype.png"
GRYPE_DOCKER_IMAGE = "alpine:latest"

# Define volume for Grype database
GRYPE_DB_VOLUME = Volume(
    name="grype_db",
    path="/root/.cache/grype"
)

# Common environment variables
COMMON_ENVS = [
    "GRYPE_DB_UPDATE",           # Controls whether Grype should update its vulnerability database
    "GRYPE_REGISTRY_INSECURE",   # Allow connections to insecure registries
    "GRYPE_SEARCH_UNINDEXED",    # Search all possible packages
    "OPENSHIFT_URL",             # OpenShift cluster URL
    "OPENSHIFT_USERNAME",        # OpenShift username
]

COMMON_FILES = []

# Define required secrets
COMMON_SECRETS = [
    "vendor_credentials",
    "OPENSHIFT_PASSWORD"         # OpenShift password
]

class GrypeTool(Tool):
    def __init__(
        self,
        name: str,
        description: str,
        content: str,
        args: list[Arg] = [],
        env: list[str] = [],
        secrets: list[str] = [],
        long_running=False,
    ):
        enhanced_content = f"""
#!/bin/sh
set -e

# Install required tools
install_tools() {{
    echo "Installing required tools..."
    apk add --no-cache curl jq yq tar gzip podman fuse-overlayfs &>/dev/null || {{
        echo "Failed to install required tools"
        exit 1
    }}
    
    # Install OpenShift CLI
    echo "Installing OpenShift CLI..."
    OC_VERSION="latest"
    curl -sSfL https://mirror.openshift.com/pub/openshift-v4/clients/ocp/$OC_VERSION/openshift-client-linux.tar.gz -o oc.tar.gz || {{
        echo "Failed to download OpenShift CLI"
        exit 1
    }}
    tar xzf oc.tar.gz oc
    mv oc /usr/local/bin/
    rm oc.tar.gz
    chmod +x /usr/local/bin/oc
    
    # Install Grype
    echo "Installing Grype..."
    curl -sSfL https://raw.githubusercontent.com/anchore/grype/main/install.sh | sh -s -- -b /usr/local/bin || {{
        echo "Failed to install Grype"
        exit 1
    }}
}}

# Setup Podman
setup_podman() {{
    echo "Setting up Podman..."
    
    # Configure storage
    mkdir -p /etc/containers
    cat > /etc/containers/storage.conf <<EOF
[storage]
driver = "overlay"
runroot = "/run/containers/storage"
graphroot = "/var/lib/containers/storage"
[storage.options]
mount_program = "/usr/bin/fuse-overlayfs"
EOF

    # Setup registry auth if credentials provided
    if [ -n "$VENDOR_CREDENTIALS" ]; then
        echo "Setting up registry authentication..."
        mkdir -p /root/.config/containers
        echo "$VENDOR_CREDENTIALS" > /root/.config/containers/auth.json
    fi
}}

# Function to handle command output
handle_output() {{
    sed 's/\\x1b\\[[0-9;]*[a-zA-Z]//g' | tr -d '\\r'
}}

# Function to setup Grype database
setup_grype_db() {{
    echo "Setting up Grype database directory..."
    mkdir -p "{GRYPE_DB_VOLUME.path}"
    chmod 755 "{GRYPE_DB_VOLUME.path}"
    
    echo "Initializing/updating Grype database..."
    if ! grype db status &>/dev/null; then
        echo "Performing initial database download..."
        grype db update || {{
            echo "Failed to initialize Grype database"
            exit 1
        }}
    fi
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
setup_podman

# Login to OpenShift
echo "Logging into OpenShift..."
if ! oc login "$OPENSHIFT_URL" \\
    --username="$OPENSHIFT_USERNAME" \\
    --password="$OPENSHIFT_PASSWORD" \\
    --insecure-skip-tls-verify=true \\
    2>/dev/null | handle_output; then
    echo "Failed to login to OpenShift cluster - check your credentials and URL" | handle_output
    exit 1
fi

setup_grype_db
verify_grype
setup_vendor_credentials

echo "Starting Grype operation..."
{content}
"""
        
        kwargs = {
            'name': name,
            'description': description,
            'docker_image': GRYPE_DOCKER_IMAGE,
            'icon_url': GRYPE_ICON_URL,
            'content': enhanced_content,
            'args': args,
            'env': COMMON_ENVS,
            'files': COMMON_FILES,
            'secrets': COMMON_SECRETS,
            'volumes': [GRYPE_DB_VOLUME],
            'long_running': long_running
        }
        
        super().__init__(**kwargs) 