import os
import sys
import subprocess
import json
import time
import re

def main():
    # We no longer expect any command-line arguments
    # Remove code that parses sys.argv[1]

    # Ensure terraform.tfvars.json exists
    if not os.path.exists('terraform.tfvars.json'):
        print("❌ Error: terraform.tfvars.json not found. Please run prepare_tfvars.py first.", file=sys.stderr)
        sys.exit(1)
    
    # Proceed with initializing and running terraform commands
    try:
        # Initialize Terraform
        print("🔄 Initializing Terraform...")
        run_command(["terraform", "init"])

        # Generate plan
        print("📋 Generating plan...")
        plan_output = run_command(
            ["terraform", "plan", "-no-color"],
            capture_output=True
        )
        print("✅ Plan generated successfully.\n")
        print(plan_output)

        # Additional logic if needed

    except Exception as e:
        error_msg = str(e)
        print(f"❌ Error: {error_msg}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main() 