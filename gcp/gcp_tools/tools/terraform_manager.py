from kubiya_sdk.tools import Arg
from .base import GCPTool, register_gcp_tool

gcp_terraform_bucket_create = GCPTool(
    name="gcp_terraform_bucket_create",
    description="Create a GCP bucket using Terraform and save the configuration to GitLab",
    content=r"""
#!/bin/bash
set -e

echo "Starting Terraform-based bucket creation process..."

# Create temporary directory for Terraform files
TEMP_DIR=$(mktemp -d)
cd "$TEMP_DIR"

# Create Terraform configuration file
cat > main.tf << 'EOL'
terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 4.0"
    }
  }
  backend "gcs" {
    bucket = "$tf_state_bucket"
    prefix = "terraform/state/$bucket_name"
  }
}

provider "google" {
  project = "$project_id"
}

resource "google_storage_bucket" "bucket" {
  name          = "$bucket_name"
  location      = "$location"
  force_destroy = $force_destroy
  
  versioning {
    enabled = $versioning_enabled
  }
  
  lifecycle_rule {
    condition {
      age = $lifecycle_age
    }
    action {
      type = "Delete"
    }
  }
}

output "bucket_url" {
  value = google_storage_bucket.bucket.url
}
EOL

# Replace variables in the Terraform file
sed -i "s/\$bucket_name/$bucket_name/g" main.tf
sed -i "s/\$location/$location/g" main.tf
sed -i "s/\$project_id/$project_id/g" main.tf
sed -i "s/\$tf_state_bucket/$tf_state_bucket/g" main.tf
sed -i "s/\$force_destroy/$force_destroy/g" main.tf
sed -i "s/\$versioning_enabled/$versioning_enabled/g" main.tf
sed -i "s/\$lifecycle_age/$lifecycle_age/g" main.tf

# Initialize Terraform
echo "Initializing Terraform..."
terraform init

# Run Terraform plan
echo "Running Terraform plan..."
terraform plan -out=tfplan

# Apply Terraform configuration
echo "Applying Terraform configuration..."
terraform apply -auto-approve tfplan

# Save Terraform configuration to GitLab
echo "Saving Terraform configuration to GitLab..."

# Clone the GitLab repository
git config --global user.email "$git_email"
git config --global user.name "$git_username"

# Clone repository with token authentication
git clone https://${git_username}:${git_token}@${gitlab_repo_url#https://} repo
cd repo

# Create directory structure if it doesn't exist
mkdir -p "terraform/buckets/$bucket_name"
cp "$TEMP_DIR/main.tf" "terraform/buckets/$bucket_name/"

# Commit and push changes
git add "terraform/buckets/$bucket_name/main.tf"
git commit -m "Add Terraform configuration for bucket $bucket_name"
git push

echo "Bucket creation completed successfully. Configuration saved to GitLab."
echo "Bucket URL: $(terraform -chdir="$TEMP_DIR" output -raw bucket_url)"

# Clean up
rm -rf "$TEMP_DIR"
""",
    args=[
        Arg(name="bucket_name", type="str", description="Name of the bucket to create", required=True),
        Arg(name="location", type="str", description="Location for the bucket (e.g., US, EU, us-central1)", required=True),
        Arg(name="project_id", type="str", description="GCP Project ID", required=True),
        Arg(name="tf_state_bucket", type="str", description="Bucket name for storing Terraform state", required=True),
        Arg(name="gitlab_repo_url", type="str", description="GitLab repository URL", required=True),
        Arg(name="git_username", type="str", description="GitLab username", required=True),
        Arg(name="git_email", type="str", description="GitLab email", required=True),
        Arg(name="git_token", type="str", description="GitLab personal access token", required=True),
        Arg(name="force_destroy", type="bool", description="Allow bucket to be destroyed even if it contains objects", default=False),
        Arg(name="versioning_enabled", type="bool", description="Enable object versioning", default=True),
        Arg(name="lifecycle_age", type="int", description="Number of days after which objects are deleted", default=90),
    ],
    long_running=True,
    mermaid_diagram="""
graph TD
    A[Start] --> B[Create Terraform Configuration]
    B --> C[Initialize Terraform]
    C --> D[Run Terraform Plan]
    D --> E[Apply Terraform Configuration]
    E --> F[Clone GitLab Repository]
    F --> G[Save Terraform Code to Repository]
    G --> H[Commit and Push Changes]
    H --> I[Clean Up]
    I --> J[End]
"""
)

gcp_terraform_bucket_permissions_check = GCPTool(
    name="gcp_terraform_bucket_permissions_check",
    description="Check if user has permissions to create a bucket in the specified project",
    content=r"""
#!/bin/bash
set -e

echo "Checking permissions for bucket creation in project $project_id..."

# Get the service account email from credentials
SERVICE_ACCOUNT=$(jq -r '.client_email' "$GOOGLE_APPLICATION_CREDENTIALS")
echo "Service account: $SERVICE_ACCOUNT"

# Check if the service account has storage.buckets.create permission
echo "Checking for storage.buckets.create permission..."
if gcloud projects get-iam-policy "$project_id" --format=json | \
   jq --arg sa "$SERVICE_ACCOUNT" '.bindings[] | select(.role | contains("storage.admin") or contains("storage.objectAdmin") or contains("owner") or contains("editor")) | .members[] | select(. == "serviceAccount:" + $sa)' | \
   grep -q .; then
    echo "Permission check passed: Service account has sufficient permissions to create buckets"
    
    # Check if the project exists and is accessible
    if gcloud projects describe "$project_id" &>/dev/null; then
        echo "Project check passed: Project $project_id exists and is accessible"
        
        # Check if the team is allowed to create buckets in this project
        if [[ "$project_id" == *"$team_id"* ]]; then
            echo "Team check passed: Team $team_id is allowed to create buckets in project $project_id"
            echo "All checks passed. You have permission to create a bucket in this project."
            exit 0
        else
            echo "Team check failed: Team $team_id is not allowed to create buckets in project $project_id"
            echo "Teams can only create buckets in projects that belong to their team."
            exit 1
        fi
    else
        echo "Project check failed: Project $project_id does not exist or is not accessible"
        exit 1
    fi
else
    echo "Permission check failed: Service account does not have sufficient permissions to create buckets"
    echo "Required permissions: storage.buckets.create (via roles like Storage Admin, Storage Object Admin, Owner, or Editor)"
    exit 1
fi
""",
    args=[
        Arg(name="project_id", type="str", description="GCP Project ID", required=True),
        Arg(name="team_id", type="str", description="Team ID to check permissions against", required=True),
    ],
    mermaid_diagram="""
graph TD
    A[Start] --> B[Get Service Account from Credentials]
    B --> C[Check for storage.buckets.create Permission]
    C --> D{Has Permission?}
    D -->|Yes| E[Check Project Exists]
    D -->|No| F[Permission Denied]
    E --> G{Project Exists?}
    G -->|Yes| H[Check Team Permission]
    G -->|No| I[Project Not Found]
    H --> J{Team Allowed?}
    J -->|Yes| K[All Checks Passed]
    J -->|No| L[Team Not Allowed]
    F --> M[End]
    I --> M
    L --> M
    K --> M
"""
)

for tool in [gcp_terraform_bucket_create, gcp_terraform_bucket_permissions_check]:
    register_gcp_tool(tool) 