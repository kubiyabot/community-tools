from kubiya_sdk.tools import Arg
from .base import GCPTool, register_gcp_tool

terraform_deploy_bucket = GCPTool(
    name="terraform_deploy_bucket",
    description="Deploy a GCP Storage bucket using Terraform",
    content="""
# Install Terraform
echo "Installing Terraform..."
apt-get update && apt-get install -y wget unzip
wget https://releases.hashicorp.com/terraform/1.5.7/terraform_1.5.7_linux_amd64.zip
unzip terraform_1.5.7_linux_amd64.zip
mv terraform /usr/local/bin/
terraform --version

# Create a directory for Terraform files
TERRAFORM_DIR=$(mktemp -d)
cd "$TERRAFORM_DIR"

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

# Initialize Terraform
terraform init

# Apply the Terraform configuration
terraform apply -auto-approve

# Show the created resources
terraform show

# Output the state
terraform state list
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
    H --> I[List Terraform State]
    I --> J[End]
"""
)

# Example of a more general Terraform deployment tool
terraform_deploy_resource = GCPTool(
    name="terraform_deploy_resource",
    description="Deploy any GCP resource using Terraform",
    content="""
# Install Terraform
echo "Installing Terraform..."
apt-get update && apt-get install -y wget unzip
wget https://releases.hashicorp.com/terraform/1.5.7/terraform_1.5.7_linux_amd64.zip
unzip terraform_1.5.7_linux_amd64.zip
mv terraform /usr/local/bin/
terraform --version

# Create a directory for Terraform files
TERRAFORM_DIR=$(mktemp -d)
cd "$TERRAFORM_DIR"

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

# Initialize Terraform
terraform init

# Apply the Terraform configuration
terraform apply -auto-approve

# Show the created resources
terraform show

# Output the state
terraform state list
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
    H --> I[List Terraform State]
    I --> J[End]
"""
)

for tool in [terraform_deploy_bucket, terraform_deploy_resource]:
    register_gcp_tool(tool) 