from kubiya_sdk.tools import Arg
from kubiya_sdk.tools.registry import tool_registry
from .base import ZoomTool

# Create Meeting Tool
create_meeting_tool = ZoomTool(
    name="create-zoom-meeting",
    description="""Create a new Zoom meeting with specified parameters.
    
Example usage:""",
    mermaid="""
    sequenceDiagram
        participant U as User 👤
        participant Z as Zoom API 🎥
        participant M as Meeting 📅

        U->>+Z: Create Meeting Request
        Z->>+M: Initialize Meeting
        M-->>-Z: Meeting Created
        Z-->>-U: Meeting Details ✅

        Note over U,M: Returns meeting ID,<br/>join URL and password
    """,
    content="""
        #!/usr/bin/env python3
        from zoom_helpers import get_zoom_client, handle_zoom_response, format_meeting_details
        import os
        
        print("*Please wait while we set up your meeting...*\n")
        
        client = get_zoom_client()
        
        meeting_settings = {
            "topic": os.environ.get('topic', 'Scheduled Meeting'),
            "type": 2,  # Scheduled meeting
            "start_time": os.environ.get('start_time'),
            "duration": int(os.environ.get('duration', 60)),
            "timezone": os.environ.get('timezone', 'UTC'),
            "password": os.environ.get('password', ''),
            "settings": {
                "host_video": os.environ.get('host_video', 'true').lower() == 'true',
                "participant_video": os.environ.get('participant_video', 'true').lower() == 'true',
                "join_before_host": os.environ.get('join_before_host', 'false').lower() == 'true',
                "mute_upon_entry": os.environ.get('mute_upon_entry', 'false').lower() == 'true',
                "waiting_room": os.environ.get('waiting_room', 'true').lower() == 'true'
            }
        }
        
        response = client.meeting.create(user_id='me', **meeting_settings)
        data = handle_zoom_response(response, "Meeting created successfully! 🎉")
        
        print(format_meeting_details(data))
        
        print("\n> 💡 **Tip**: Share the join URL and password with your participants")
    """,
    args=[
        Arg(name="topic", description="Meeting topic/name", required=True),
        Arg(name="start_time", description="Meeting start time (YYYY-MM-DD HH:MM:SS)", required=True),
        Arg(name="duration", description="Meeting duration in minutes", required=False, default="60"),
        Arg(name="timezone", description="Meeting timezone", required=False, default="UTC"),
        Arg(name="password", description="Meeting password", required=False),
        Arg(name="host_video", description="Start with host video on", required=False, default="true"),
        Arg(name="participant_video", description="Start with participant video on", required=False, default="true"),
        Arg(name="join_before_host", description="Allow participants to join before host", required=False, default="false"),
        Arg(name="mute_upon_entry", description="Mute participants upon entry", required=False, default="false"),
        Arg(name="waiting_room", description="Enable waiting room", required=False, default="true"),
    ]
)

# Meeting Controls Tool
meeting_controls_tool = ZoomTool(
    name="control-zoom-meeting",
    description="Control an ongoing Zoom meeting (mute all, remove participant, etc)",
    mermaid="""
    sequenceDiagram
        participant H as Host 👑
        participant Z as Zoom API 🎥
        participant P as Participants 👥

        H->>+Z: Control Request
        alt Mute All
            Z->>P: Mute Command
            P-->>Z: Muted ✅
        else Remove Participant
            Z->>P: Remove Command
            P-->>Z: Removed ⛔
        end
        Z-->>-H: Action Completed
    """,
    content="""
        #!/usr/bin/env python3
        from zoom_helpers import get_zoom_client, handle_zoom_response, format_meeting_control_result
        import os
        
        client = get_zoom_client()
        meeting_id = os.environ['meeting_id']
        action = os.environ['action']
        
        print(f"### 🎮 Executing Meeting Control")
        print(f"**Action**: `{action}`")
        print("*Processing your request...*\n")
        
        try:
            if action == "mute_all":
                response = client.meeting.update(
                    meeting_id=meeting_id,
                    settings={"mute_upon_entry": True}
                )
                print(format_meeting_control_result('mute_all'))
                
            elif action == "unmute_all":
                response = client.meeting.update(
                    meeting_id=meeting_id,
                    settings={"mute_upon_entry": False}
                )
                print(format_meeting_control_result('unmute_all'))
                
            elif action == "end_meeting":
                response = client.meeting.end(meeting_id=meeting_id)
                print(format_meeting_control_result('end_meeting'))
                
            elif action.startswith("remove_"):
                participant_id = action.split("_")[1]
                response = client.meeting.participant_remove(
                    meeting_id=meeting_id,
                    participant_id=participant_id
                )
                print(format_meeting_control_result('remove'))
            
            handle_zoom_response(response, "Control action executed successfully")
            
        except Exception as e:
            print(format_meeting_control_result(action, success=False))
            print(f"**Error Details**: {str(e)}")
            exit(1)
    """,
    args=[
        Arg(name="meeting_id", description="ID of the meeting to control", required=True),
        Arg(name="action", description="Control action (mute_all, unmute_all, end_meeting, remove_<participant_id>)", required=True),
    ]
)

# List Recordings Tool
list_recordings_tool = ZoomTool(
    name="list-zoom-recordings",
    description="List all recordings for a specific date range",
    mermaid="""
    flowchart TD
        Z[Zoom API] --> R1[Recording 1 📹]
        Z --> R2[Recording 2 📹]
        Z --> R3[Recording 3 📹]
        
        R1 --> D1[Download URL]
        R1 --> I1[Meeting Info]
        
        R2 --> D2[Download URL]
        R2 --> I2[Meeting Info]
        
        R3 --> D3[Download URL]
        R3 --> I3[Meeting Info]
        
        style Z fill:#f96,stroke:#333,stroke-width:4px
        style R1 fill:#bbf,stroke:#333
        style R2 fill:#bbf,stroke:#333
        style R3 fill:#bbf,stroke:#333
    """,
    content="""
        #!/usr/bin/env python3
        from zoom_helpers import get_zoom_client, handle_zoom_response, format_recording_details, validate_date
        import os
        from datetime import datetime
        
        client = get_zoom_client()
        
        start_date = os.environ['start_date']
        end_date = os.environ.get('end_date', datetime.now().strftime('%Y-%m-%d'))
        
        # Validate dates
        validate_date(start_date)
        validate_date(end_date)
        
        print(f"### 📹 Fetching Zoom Recordings")
        print(f"**Period**: `{start_date}` to `{end_date}`")
        print("*Please wait while we retrieve your recordings...*\n")
        
        response = client.recording.list(
            user_id='me',
            start=start_date,
            end=end_date
        )
        
        data = handle_zoom_response(response, "Recordings retrieved successfully")
        print(format_recording_details(data.get('meetings', [])))
    """,
    args=[
        Arg(name="start_date", description="Start date for recordings (YYYY-MM-DD)", required=True),
        Arg(name="end_date", description="End date for recordings (YYYY-MM-DD)", required=False),
    ]
)

# Register all tools
tool_registry.register("zoom", create_meeting_tool)
tool_registry.register("zoom", meeting_controls_tool)
tool_registry.register("zoom", list_recordings_tool) 