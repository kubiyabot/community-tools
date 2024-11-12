#!/usr/bin/env python3
import os
import sys

try:
    sys.path.append('/tmp')
    from zoom_tools.zoom_operations import create_webinar
except ImportError:
    print("### ⚠️ Note: This is likely a discovery call without the tool environment")
    print("Required modules will be available during actual tool execution")
    # Create dummy function for discovery
    def create_webinar(*args, **kwargs): pass

def main():
    """Main handler for webinar operations"""
    if len(sys.argv) < 2:
        print("❌ Error: Operation type required (create)")
        exit(1)

    operation = sys.argv[1]
    
    try:
        if operation == "create":
            settings = {k: v for k, v in os.environ.items() if not k.startswith('_')}
            print(create_webinar(settings))
        else:
            print(f"❌ Error: Unknown operation '{operation}'")
            exit(1)
    except Exception as e:
        print(f"❌ Error executing operation: {str(e)}")
        exit(1)

if __name__ == "__main__":
    main() 