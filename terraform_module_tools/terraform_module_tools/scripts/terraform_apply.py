#!/usr/bin/env python3
import os
import sys
import subprocess

def main():
    # No longer expect any command-line arguments

    # Ensure terraform.tfvars.json exists
    if not os.path.exists('terraform.tfvars.json'):
        print("❌ Error: terraform.tfvars.json not found. Please run prepare_tfvars.py first.", file=sys.stderr)
        sys.exit(1)

    try:
        # Initialize Terraform
        print("🔄 Initializing Terraform...")
        subprocess.run(["terraform", "init"], check=True)

        # Apply the changes
        print("🚀 Applying changes...")
        subprocess.run(["terraform", "apply", "-auto-approve"], check=True)

        # Confirm success
        print("✅ Terraform apply completed successfully.")

    except subprocess.CalledProcessError as e:
        error_msg = str(e)
        print(f"❌ Error during terraform apply: {error_msg}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main() 