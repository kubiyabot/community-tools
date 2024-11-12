#!/usr/bin/env python3
import os
import sys

try:
    sys.path.append('/tmp')
    from zoom_tools.zoom_operations import create_meeting, control_meeting, list_recordings
except ImportError:
    print("### ⚠️ Note: This is likely a discovery call without the tool environment")
    print("Required modules will be available during actual tool execution")
    # Create dummy functions for discovery
    def create_meeting(*args, **kwargs): pass
    def control_meeting(*args, **kwargs): pass
    def list_recordings(*args, **kwargs): pass

def main():
    """Main handler for meeting operations"""
    if len(sys.argv) < 2:
        print("❌ Error: Operation type required (create/control/recordings)")
        exit(1)

    operation = sys.argv[1]
    
    try:
        if operation == "create":
            settings = {k: v for k, v in os.environ.items() if not k.startswith('_')}
            print(create_meeting(settings))
        elif operation == "control":
            print(control_meeting(os.environ['meeting_id'], os.environ['action']))
        elif operation == "recordings":
            print(list_recordings(
                os.environ['start_date'],
                os.environ.get('end_date')
            ))
        else:
            print(f"❌ Error: Unknown operation '{operation}'")
            exit(1)
    except Exception as e:
        print(f"❌ Error executing operation: {str(e)}")
        exit(1)

if __name__ == "__main__":
    main() 