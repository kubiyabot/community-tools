#!/usr/bin/env python3
import os
import sys
sys.path.append('/tmp')
from zoom_tools.zoom_operations import list_users

def main():
    """Main handler for user operations"""
    if len(sys.argv) < 2:
        print("❌ Error: Operation type required (list)")
        exit(1)

    operation = sys.argv[1]
    
    if operation == "list":
        print(list_users(os.environ.get('status', 'active')))
    else:
        print(f"❌ Error: Unknown operation '{operation}'")
        exit(1)

if __name__ == "__main__":
    main() 