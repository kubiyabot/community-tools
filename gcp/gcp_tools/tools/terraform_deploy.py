from kubiya_sdk.tools import Arg
from .base import TerraformTool, register_gcp_tool

terraform_deploy_bucket = TerraformTool(
    name="terraform_deploy_bucket",
    description="Deploy a GCP Storage bucket using Terraform and append to existing configuration in GitLab",
    content=f"""
# Make sure we have essential tools
echo "Installing essential tools..."
apk update --quiet && apk add --quiet --no-cache wget unzip git > /dev/null 2>&1

# Install Terraform
echo "Installing Terraform..."
wget -q https://releases.hashicorp.com/terraform/1.5.7/terraform_1.5.7_linux_amd64.zip
unzip -q terraform_1.5.7_linux_amd64.zip
mv terraform /usr/local/bin/
echo "Terraform $(terraform --version | head -n 1 | awk '{{print $2}}') installed successfully"

# Create a directory for Terraform files
TERRAFORM_DIR=$(mktemp -d)
cd "$TERRAFORM_DIR"
echo "Working in temporary directory: $TERRAFORM_DIR"

# Create provider configuration for GCP
cat > provider.tf << EOF
provider "google" {{
  project     = "$GOOGLE_PROJECT"
  region      = "$region"
}}

terraform {{
  required_providers {{
    google = {{
      source  = "hashicorp/google"
      version = "~> 4.0"
    }}
  }}
}}
EOF

# Format the terraform_content to ensure proper syntax
# Replace single-line format with multi-line format for multiple arguments
FORMATTED_CONTENT=$(echo "$terraform_content" | sed 's/{{ *name *= *"\\([^"]*\\)" *, *location *= *"\\([^"]*\\)" *}}/{{\\n  name     = "\\1"\\n  location = "\\2"\\n}}/')

# Create a temporary main.tf file with the provided Terraform content
echo "$FORMATTED_CONTENT" > main.tf
echo "Created Terraform configuration files"

# Initialize Terraform
echo "Initializing Terraform..."
terraform init -input=false -no-color > /dev/null
INIT_STATUS=$?
if [ $INIT_STATUS -ne 0 ]; then
    echo "ERROR: Terraform initialization failed with status $INIT_STATUS"
    exit $INIT_STATUS
fi
echo "Terraform initialized successfully"

# Apply the Terraform configuration
echo "Applying Terraform configuration to create bucket '$bucket_name'..."
terraform apply -auto-approve -input=false -no-color > /dev/null
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
    
    # Check if main.tf already exists, if not create it with proper header
    if [ ! -f "$BUCKETS_DIR/main.tf" ]; then
        cat > "$BUCKETS_DIR/main.tf" << EOF
# GCP Storage Buckets Terraform Configuration
# Last updated: $(date +%Y-%m-%d)
# Managed by: Cloud Infrastructure Team

locals {{
  default_labels = {{
    environment = "staging"
    managed_by  = "terraform"
    team        = "platform-engineering"
  }}
  
  default_lifecycle_rules = {{
    standard = {{
      age          = 90
      storage_class = "NEARLINE"
    }}
    archive = {{
      age          = 365
      storage_class = "COLDLINE"
    }}
  }}
}}
EOF
    fi
    
    # Check if provider.tf already exists, if not copy from existing
    if [ ! -f "$BUCKETS_DIR/provider.tf" ]; then
        cp provider.tf "$BUCKETS_DIR/provider.tf"
    fi
    
    # Generate a resource name that's valid for Terraform
    RESOURCE_NAME=$(echo "$bucket_name" | tr '-' '_')
    
    # Check if bucket already exists in the configuration
    if grep -q "resource \\"google_storage_bucket\\" \\"$RESOURCE_NAME\\"" "$BUCKETS_DIR/main.tf"; then
        echo "Bucket '$bucket_name' already exists in Terraform configuration, updating..."
        # Create a backup of the current main.tf
        cp "$BUCKETS_DIR/main.tf" "$BUCKETS_DIR/main.tf.bak.$(date +%Y%m%d%H%M%S)"
        
        # Remove the existing bucket configuration (from resource line to closing brace)
        sed -i "/# Bucket: $bucket_name/,/^}}/d" "$BUCKETS_DIR/main.tf"
    fi
    
    # Modify the terraform_content to use the proper resource name and include labels
    MODIFIED_CONTENT=$(echo "$terraform_content" | sed "s/resource \\"google_storage_bucket\\" \\"bucket\\"/resource \\"google_storage_bucket\\" \\"$RESOURCE_NAME\\"/")
    
    # Check if labels are already in the content, if not add them
    if ! echo "$MODIFIED_CONTENT" | grep -q "labels"; then
        # Add labels before the closing brace
        MODIFIED_CONTENT=$(echo "$MODIFIED_CONTENT" | sed "s/}}/\\n  labels = merge(local.default_labels, {{\\n    purpose = \\"application-data\\"\\n    owner   = \\"$(whoami)\\"\\n  }})\\n}}/")
    fi
    
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
    
    # Update outputs.tf file to include the new bucket
    if [ -f "$BUCKETS_DIR/outputs.tf" ]; then
        # Create a new temporary file for the updated outputs
        TEMP_OUTPUTS_FILE=$(mktemp)
        
        # Write the updated outputs.tf content to the temporary file
        cat > "$TEMP_OUTPUTS_FILE" << EOF
# Output the bucket names and URLs for use in other modules

output "bucket_names" {{
  description = "Map of bucket names"
  value = {{
EOF
        
        # Add existing bucket names from the current outputs.tf
        grep -A 20 "output \"bucket_names\"" "$BUCKETS_DIR/outputs.tf" | 
        grep -v "output \"bucket_names\"" | 
        grep -v "description" | 
        grep -v "value = {{" | 
        grep -v "}}" | 
        grep -v "^$" | 
        grep -v "^#" >> "$TEMP_OUTPUTS_FILE" || true
        
        # Add the new bucket name with proper syntax for Terraform
        echo "    $RESOURCE_NAME = google_storage_bucket.$RESOURCE_NAME.name" >> "$TEMP_OUTPUTS_FILE"
        echo "  }}" >> "$TEMP_OUTPUTS_FILE"
        echo "}}" >> "$TEMP_OUTPUTS_FILE"
        echo "" >> "$TEMP_OUTPUTS_FILE"
        
        # Add bucket URLs output
        cat >> "$TEMP_OUTPUTS_FILE" << EOF
output "bucket_urls" {{
  description = "Map of bucket URLs"
  value = {{
    $RESOURCE_NAME = "gs://\${{google_storage_bucket.$RESOURCE_NAME.name}}"
  }}
}}
EOF
        
        # Add existing bucket URLs from the current outputs.tf
        grep -A 20 "output \"bucket_urls\"" "$BUCKETS_DIR/outputs.tf" | 
        grep -v "output \"bucket_urls\"" | 
        grep -v "description" | 
        grep -v "value = {{" | 
        grep -v "}}" | 
        grep -v "^$" | 
        grep -v "^#" >> "$TEMP_OUTPUTS_FILE" || true
        
        # Add the new bucket URL with properly escaped interpolation syntax for shell script
        echo "    $RESOURCE_NAME = \"gs://\${{google_storage_bucket.$RESOURCE_NAME.name}}\"" >> "$TEMP_OUTPUTS_FILE"
        echo "  }}" >> "$TEMP_OUTPUTS_FILE"
        echo "}}" >> "$TEMP_OUTPUTS_FILE"
        
        # Add bucket self links output
        cat >> "$TEMP_OUTPUTS_FILE" << EOF
output "bucket_self_links" {{
  description = "Map of bucket self links"
  value = {{
EOF
        
        # Add existing bucket self links from the current outputs.tf
        grep -A 20 "output \"bucket_self_links\"" "$BUCKETS_DIR/outputs.tf" | 
        grep -v "output \"bucket_self_links\"" | 
        grep -v "description" | 
        grep -v "value = {{" | 
        grep -v "}}" | 
        grep -v "^$" | 
        grep -v "^#" >> "$TEMP_OUTPUTS_FILE" || true
        
        # Add the new bucket self link
        echo "    $RESOURCE_NAME = google_storage_bucket.$RESOURCE_NAME.self_link" >> "$TEMP_OUTPUTS_FILE"
        echo "  }}" >> "$TEMP_OUTPUTS_FILE"
        echo "}}" >> "$TEMP_OUTPUTS_FILE"
        
        # Replace the original outputs.tf with our new file
        mv "$TEMP_OUTPUTS_FILE" "$BUCKETS_DIR/outputs.tf"
        
    else
        # Create a new outputs.tf file with properly escaped Terraform interpolation
        cat > "$BUCKETS_DIR/outputs.tf" << EOF
# Output the bucket names and URLs for use in other modules

output "bucket_names" {{
  description = "Map of bucket names"
  value = {{
    $RESOURCE_NAME = google_storage_bucket.$RESOURCE_NAME.name
  }}
}}

output "bucket_urls" {{
  description = "Map of bucket URLs"
  value = {{
    $RESOURCE_NAME = "gs://\${{google_storage_bucket.$RESOURCE_NAME.name}}"
  }}
}}

output "bucket_self_links" {{
  description = "Map of bucket self links"
  value = {{
    $RESOURCE_NAME = google_storage_bucket.$RESOURCE_NAME.self_link
  }}
}}
EOF
    fi
    
    # Commit and push changes
    cd "$REPO_DIR"
    git add .
    git commit -m "Update Terraform configuration for bucket $bucket_name"
    git push
    
    echo "Successfully saved Terraform configuration to GitLab at $BUCKETS_DIR"
    
    # Update Terraform state in GCP
    echo "Using Terraform state in GCS bucket defined in provider.tf"
    
    # Initialize with existing backend config
    cd "$BUCKETS_DIR"
    terraform init -reconfigure
    
    # Import the resource into the state if it's not already there
    if ! terraform state list | grep -q "google_storage_bucket.$RESOURCE_NAME"; then
        terraform import google_storage_bucket.$RESOURCE_NAME $bucket_name
        echo "Imported $bucket_name into Terraform state"
    else
        echo "Bucket $bucket_name already exists in Terraform state"
    fi
    
    echo "Terraform state updated successfully"
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
    I --> J[Update Terraform State in GCS]
    J --> K[Output Success Message]
    K --> L[End]
"""
)

for tool in [terraform_deploy_bucket]:
    register_gcp_tool(tool)