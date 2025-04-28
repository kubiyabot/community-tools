from kubiya_sdk.tools import Arg
from .base import GCPTool, register_gcp_tool

terraform_deploy_bucket = GCPTool(
    name="terraform_deploy_bucket",
    description="Deploy a GCP Storage bucket using Terraform",
    content="""
# Install Terraform quietly
echo "Installing Terraform..."
apt-get update -qq && apt-get install -y -qq wget unzip > /dev/null 2>&1
wget -q https://releases.hashicorp.com/terraform/1.5.7/terraform_1.5.7_linux_amd64.zip
unzip -q terraform_1.5.7_linux_amd64.zip
mv terraform /usr/local/bin/
echo "Terraform $(terraform --version | head -n 1) installed successfully"

# Create a directory for Terraform files
TERRAFORM_DIR=$(mktemp -d)
cd "$TERRAFORM_DIR"
echo "Working in temporary directory: $TERRAFORM_DIR"

# Create provider configuration for GCP
cat > provider.tf << EOF
provider "google" {
  credentials = file("$CREDS_FILE")
  project     = "$(gcloud config get-value project)"
  region      = "$region"
}
EOF

# Create the main.tf file with the provided Terraform content
echo "$terraform_content" > main.tf
echo "Created Terraform configuration files"

# Initialize Terraform with reduced output
echo "Initializing Terraform..."
terraform init -no-color -input=false > terraform_init.log 2>&1
INIT_STATUS=$?
if [ $INIT_STATUS -ne 0 ]; then
    echo "ERROR: Terraform initialization failed with status $INIT_STATUS"
    cat terraform_init.log
    exit $INIT_STATUS
fi
echo "Terraform initialized successfully"

# Apply the Terraform configuration
echo "Applying Terraform configuration to create bucket '$bucket_name'..."
terraform apply -auto-approve -no-color -input=false > terraform_apply.log 2>&1
APPLY_STATUS=$?
if [ $APPLY_STATUS -ne 0 ]; then
    echo "ERROR: Terraform apply failed with status $APPLY_STATUS"
    cat terraform_apply.log
    exit $APPLY_STATUS
fi
echo "Terraform apply completed successfully"

# Show the created resources
echo "Resources created:"
terraform state list

# Output success message
echo "SUCCESS: GCP Storage bucket '$bucket_name' has been deployed successfully in region '$region'"
""",
    args=[
        Arg(name="bucket_name", type="str", description="Name of the bucket to create", required=True),
        Arg(name="region", type="str", description="Region for the bucket (e.g., us-central1)", required=True),
        Arg(name="terraform_content", type="str", description="Terraform configuration content", required=True),
    ],
    mermaid_diagram="""
graph TD
    A[Start] --> B[Install Terraform]
    B --> C[Create Terraform Directory]
    C --> D[Configure GCP Provider]
    D --> E[Write Terraform Configuration]
    E --> F[Initialize Terraform]
    F --> G[Apply Terraform Configuration]
    G --> H[Show Created Resources]
    H --> I[Output Success Message]
    I --> J[End]
"""
)

# Example of a more general Terraform deployment tool
terraform_deploy_resource = GCPTool(
    name="terraform_deploy_resource",
    description="Deploy any GCP resource using Terraform",
    content="""
# Install Terraform quietly
echo "Installing Terraform..."
apt-get update -qq && apt-get install -y -qq wget unzip > /dev/null 2>&1
wget -q https://releases.hashicorp.com/terraform/1.5.7/terraform_1.5.7_linux_amd64.zip
unzip -q terraform_1.5.7_linux_amd64.zip
mv terraform /usr/local/bin/
echo "Terraform $(terraform --version | head -n 1) installed successfully"

# Create a directory for Terraform files
TERRAFORM_DIR=$(mktemp -d)
cd "$TERRAFORM_DIR"
echo "Working in temporary directory: $TERRAFORM_DIR"

# Create provider configuration for GCP
cat > provider.tf << EOF
provider "google" {
  credentials = file("$CREDS_FILE")
  project     = "$(gcloud config get-value project)"
  region      = "$region"
}
EOF

# Create the main.tf file with the provided Terraform content
echo "$terraform_content" > main.tf
echo "Created Terraform configuration files"

# Initialize Terraform with reduced output
echo "Initializing Terraform..."
terraform init -no-color -input=false > terraform_init.log 2>&1
INIT_STATUS=$?
if [ $INIT_STATUS -ne 0 ]; then
    echo "ERROR: Terraform initialization failed with status $INIT_STATUS"
    cat terraform_init.log
    exit $INIT_STATUS
fi
echo "Terraform initialized successfully"

# Apply the Terraform configuration
echo "Applying Terraform configuration to create $resource_type '$resource_name'..."
terraform apply -auto-approve -no-color -input=false > terraform_apply.log 2>&1
APPLY_STATUS=$?
if [ $APPLY_STATUS -ne 0 ]; then
    echo "ERROR: Terraform apply failed with status $APPLY_STATUS"
    cat terraform_apply.log
    exit $APPLY_STATUS
fi
echo "Terraform apply completed successfully"

# Show the created resources
echo "Resources created:"
terraform state list

# Output success message
echo "SUCCESS: GCP $resource_type '$resource_name' has been deployed successfully in region '$region'"
""",
    args=[
        Arg(name="resource_type", type="str", description="Type of GCP resource to create", required=True),
        Arg(name="resource_name", type="str", description="Name of the resource to create", required=True),
        Arg(name="terraform_content", type="str", description="Terraform configuration content", required=True),
        Arg(name="region", type="str", description="GCP region for deployment", required=True),
    ],
    mermaid_diagram="""
graph TD
    A[Start] --> B[Install Terraform]
    B --> C[Create Terraform Directory]
    C --> D[Configure GCP Provider]
    D --> E[Write Terraform Configuration]
    E --> F[Initialize Terraform]
    F --> G[Apply Terraform Configuration]
    G --> H[Show Created Resources]
    H --> I[Output Success Message]
    I --> J[End]
"""
)

for tool in [terraform_deploy_bucket, terraform_deploy_resource]:
    register_gcp_tool(tool) 