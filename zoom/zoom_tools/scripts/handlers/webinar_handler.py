#!/usr/bin/env python3
import os
import sys
sys.path.append('/tmp')
from zoom_tools.zoom_operations import create_webinar

def main():
    """Main handler for webinar operations"""
    if len(sys.argv) < 2:
        print("❌ Error: Operation type required (create)")
        exit(1)

    operation = sys.argv[1]
    
    if operation == "create":
        settings = {k: v for k, v in os.environ.items() if not k.startswith('_')}
        print(create_webinar(settings))
    else:
        print(f"❌ Error: Unknown operation '{operation}'")
        exit(1)

if __name__ == "__main__":
    main() 