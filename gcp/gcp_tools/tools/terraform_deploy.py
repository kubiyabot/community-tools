from kubiya_sdk.tools import Arg
from .base import GCPTool, register_gcp_tool

terraform_deploy_bucket = GCPTool(
    name="terraform_deploy_bucket",
    description="Deploy a GCP Storage bucket using Terraform and append to existing configuration in GitLab",
    content="""
# Install Terraform quietly
echo "Installing Terraform..."
apt-get update -qq && apt-get install -y -qq wget unzip git > /dev/null 2>&1
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

terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 4.0"
    }
  }
}
EOF

# Create a temporary main.tf file with the provided Terraform content
echo "$terraform_content" > main.tf
echo "Created Terraform configuration files"

# Display the content of the files for debugging
echo "Contents of provider.tf:"
cat provider.tf
echo "Contents of main.tf:"
cat main.tf

# Initialize Terraform with more verbose output
echo "Initializing Terraform..."
terraform init -input=false
INIT_STATUS=$?
if [ $INIT_STATUS -ne 0 ]; then
    echo "ERROR: Terraform initialization failed with status $INIT_STATUS"
    exit $INIT_STATUS
fi
echo "Terraform initialized successfully"

# Apply the Terraform configuration
echo "Applying Terraform configuration to create bucket '$bucket_name'..."
terraform apply -auto-approve -input=false
APPLY_STATUS=$?
if [ $APPLY_STATUS -ne 0 ]; then
    echo "ERROR: Terraform apply failed with status $APPLY_STATUS"
    exit $APPLY_STATUS
fi
echo "Terraform apply completed successfully"

# Show the created resources
echo "Resources created:"
terraform state list

# Save Terraform configuration to GitLab
if [ -n "$GITLAB_REPO_URL" ]; then
    echo "Saving Terraform configuration to GitLab repository: $GITLAB_REPO_URL"
    
    # Configure Git
    git config --global user.email "terraform-bot@example.com"
    git config --global user.name "Terraform Bot"
    
    # Clone the repository
    REPO_DIR=$(mktemp -d)
    if [ -n "$GITLAB_TOKEN" ]; then
        # Use token for authentication
        GITLAB_URL=$(echo "$GITLAB_REPO_URL" | sed 's/https:\\/\\///')
        git clone "https://oauth2:$GITLAB_TOKEN@$GITLAB_URL" "$REPO_DIR"
    else
        # Use SSH or other configured authentication
        git clone "$GITLAB_REPO_URL" "$REPO_DIR"
    fi
    
    # Create buckets directory if it doesn't exist
    BUCKETS_DIR="$REPO_DIR/terraform/buckets"
    mkdir -p "$BUCKETS_DIR"
    
    # Check if main.tf already exists, if not create it
    if [ ! -f "$BUCKETS_DIR/main.tf" ]; then
        echo "# GCP Storage Buckets Terraform Configuration" > "$BUCKETS_DIR/main.tf"
        echo "# This file is automatically managed - do not edit directly" >> "$BUCKETS_DIR/main.tf"
        echo "" >> "$BUCKETS_DIR/main.tf"
    fi
    
    # Check if provider.tf already exists, if not create it
    if [ ! -f "$BUCKETS_DIR/provider.tf" ]; then
        cp provider.tf "$BUCKETS_DIR/provider.tf"
    fi
    
    # Check if bucket already exists in the configuration
    if grep -q "resource \"google_storage_bucket\" \"$bucket_name\"" "$BUCKETS_DIR/main.tf"; then
        echo "Bucket '$bucket_name' already exists in Terraform configuration, updating..."
        # Create a backup of the current main.tf
        cp "$BUCKETS_DIR/main.tf" "$BUCKETS_DIR/main.tf.bak.$(date +%Y%m%d%H%M%S)"
        
        # Remove the existing bucket configuration
        sed -i "/resource \"google_storage_bucket\" \"$bucket_name\"/,/}/d" "$BUCKETS_DIR/main.tf"
    fi
    
    # Append the new bucket configuration to main.tf
    # First, modify the resource name in the terraform_content to match bucket_name
    MODIFIED_CONTENT=$(echo "$terraform_content" | sed "s/resource \"google_storage_bucket\" \"bucket\"/resource \"google_storage_bucket\" \"$bucket_name\"/")
    
    # Append to main.tf with a comment indicating when it was added/updated
    echo "" >> "$BUCKETS_DIR/main.tf"
    echo "# Bucket: $bucket_name - Added/Updated on $(date)" >> "$BUCKETS_DIR/main.tf"
    echo "$MODIFIED_CONTENT" >> "$BUCKETS_DIR/main.tf"
    
    # Update or create README with deployment information
    if [ ! -f "$BUCKETS_DIR/README.md" ]; then
        cat > "$BUCKETS_DIR/README.md" << EOF
# GCP Storage Buckets

This directory contains Terraform configuration for all GCP Storage buckets.

## Structure
- main.tf: Contains all bucket definitions
- provider.tf: GCP provider configuration

## Managed Buckets
EOF
    fi
    
    # Check if bucket is already in the README
    if ! grep -q "^- $bucket_name:" "$BUCKETS_DIR/README.md"; then
        echo "- $bucket_name: Created on $(date), Region: $region" >> "$BUCKETS_DIR/README.md"
    else
        # Update the existing entry
        sed -i "s/^- $bucket_name:.*$/- $bucket_name: Updated on $(date), Region: $region/" "$BUCKETS_DIR/README.md"
    fi
    
    # Commit and push changes
    cd "$REPO_DIR"
    git add .
    git commit -m "Update Terraform configuration for bucket $bucket_name"
    git push
    
    echo "Successfully saved Terraform configuration to GitLab at $BUCKETS_DIR"
else
    echo "GitLab repository URL not provided in environment, skipping GitLab integration"
fi

# Output success message
echo "SUCCESS: GCP Storage bucket '$bucket_name' has been deployed successfully in region '$region'"
""",
    args=[
        Arg(name="bucket_name", type="str", description="Name of the bucket to create", required=True),
        Arg(name="region", type="str", description="Region for the bucket (e.g., us-central1)", required=True),
        Arg(name="terraform_content", type="str", 
            description="Terraform configuration for the bucket resource. Example: 'resource \"google_storage_bucket\" \"bucket\" { name = \"my-bucket\", location = \"us-central1\" }'", 
            required=True),
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
    H --> I[Save to GitLab]
    I --> J[Output Success Message]
    J --> K[End]
"""
)

for tool in [terraform_deploy_bucket]:
    register_gcp_tool(tool)