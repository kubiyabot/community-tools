from kubiya_sdk.tools import Arg
from kubiya_sdk.tools.registry import tool_registry
from zoom_tools.base import ZoomTool

# Create Meeting Tool
create_meeting_tool = ZoomTool(
    name="create-zoom-meeting",
    description="Create a new Zoom meeting with specified parameters",
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
        import os
        import json
        from zoomus import ZoomClient
        
        # Initialize Zoom client
        client = ZoomClient(os.environ['ZOOM_API_KEY'], os.environ['ZOOM_API_SECRET'])
        
        # Prepare meeting settings
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
        
        print("🎥 Creating Zoom meeting...")
        response = client.meeting.create(user_id='me', **meeting_settings)
        meeting_data = json.loads(response.content)
        
        if response.status_code == 201:
            print("✅ Meeting created successfully!")
            print(f"📋 Meeting Details:")
            print(f"   • Meeting ID: {meeting_data['id']}")
            print(f"   • Topic: {meeting_data['topic']}")
            print(f"   • Join URL: {meeting_data['join_url']}")
            print(f"   • Password: {meeting_data['password']}")
            print(f"   • Start Time: {meeting_data['start_time']}")
        else:
            print(f"❌ Failed to create meeting: {meeting_data.get('message', 'Unknown error')}")
            exit(1)
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
        import os
        import json
        from zoomus import ZoomClient
        
        client = ZoomClient(os.environ['ZOOM_API_KEY'], os.environ['ZOOM_API_SECRET'])
        meeting_id = os.environ['meeting_id']
        action = os.environ['action']
        
        print(f"🎮 Executing meeting control: {action}")
        
        if action == "mute_all":
            response = client.meeting.update(
                meeting_id=meeting_id,
                settings={"mute_upon_entry": True}
            )
            print("🔇 All participants muted")
            
        elif action == "unmute_all":
            response = client.meeting.update(
                meeting_id=meeting_id,
                settings={"mute_upon_entry": False}
            )
            print("🔊 All participants can now unmute")
            
        elif action == "end_meeting":
            response = client.meeting.end(meeting_id=meeting_id)
            print("🛑 Meeting ended")
            
        elif action.startswith("remove_"):
            participant_id = action.split("_")[1]
            response = client.meeting.participant_remove(
                meeting_id=meeting_id,
                participant_id=participant_id
            )
            print(f"⛔ Removed participant {participant_id}")
        
        if response.status_code in [200, 204]:
            print("✅ Action completed successfully!")
        else:
            print(f"❌ Action failed: {json.loads(response.content).get('message', 'Unknown error')}")
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
        import os
        import json
        from datetime import datetime
        from zoomus import ZoomClient
        
        client = ZoomClient(os.environ['ZOOM_API_KEY'], os.environ['ZOOM_API_SECRET'])
        
        start_date = os.environ['start_date']
        end_date = os.environ.get('end_date', datetime.now().strftime('%Y-%m-%d'))
        
        print(f"📹 Fetching recordings from {start_date} to {end_date}...")
        
        response = client.recording.list(
            user_id='me',
            start=start_date,
            end=end_date
        )
        
        recordings = json.loads(response.content)
        
        if response.status_code == 200:
            meetings = recordings.get('meetings', [])
            print(f"✅ Found {len(meetings)} recordings")
            
            for meeting in meetings:
                print(f"\n📅 Meeting: {meeting['topic']}")
                print(f"   • Date: {meeting['start_time']}")
                print(f"   • Duration: {meeting['duration']} minutes")
                
                for recording in meeting.get('recording_files', []):
                    print(f"   • Recording Type: {recording['recording_type']}")
                    print(f"   • Size: {recording['file_size'] / 1024 / 1024:.2f} MB")
                    print(f"   • Download URL: {recording['download_url']}")
        else:
            print(f"❌ Failed to fetch recordings: {recordings.get('message', 'Unknown error')}")
            exit(1)
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