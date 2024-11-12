from kubiya_sdk.tools import Arg
from kubiya_sdk.tools.registry import tool_registry
from .base import ZoomTool

create_webinar_tool = ZoomTool(
    name="create-zoom-webinar",
    description="Create a new Zoom webinar",
    mermaid="""
    sequenceDiagram
        participant U as User 👤
        participant Z as Zoom API 🎥
        participant W as Webinar 📺

        U->>+Z: Create Webinar Request
        Z->>+W: Initialize Webinar
        W-->>-Z: Webinar Created
        Z-->>-U: Webinar Details ✅

        Note over U,W: Returns webinar ID,<br/>registration URL
    """,
    content="""
        #!/usr/bin/env python3
        from zoom_helpers import get_zoom_client, handle_zoom_response
        import os
        
        client = get_zoom_client()
        
        webinar_settings = {
            "topic": os.environ['topic'],
            "type": 5,  # Scheduled webinar
            "start_time": os.environ['start_time'],
            "duration": int(os.environ.get('duration', 60)),
            "timezone": os.environ.get('timezone', 'UTC'),
            "settings": {
                "host_video": os.environ.get('host_video', 'true').lower() == 'true',
                "panelists_video": os.environ.get('panelists_video', 'true').lower() == 'true',
                "practice_session": os.environ.get('practice_session', 'true').lower() == 'true',
                "hd_video": os.environ.get('hd_video', 'true').lower() == 'true',
                "approval_type": int(os.environ.get('approval_type', 0)),
                "registration_type": int(os.environ.get('registration_type', 1)),
                "audio": os.environ.get('audio', 'both')
            }
        }
        
        print("📺 Creating Zoom webinar...")
        response = client.webinar.create(user_id='me', **webinar_settings)
        data = handle_zoom_response(response, "Webinar created successfully")
        
        print(f"📋 Webinar Details:")
        print(f"   • Webinar ID: {data['id']}")
        print(f"   • Topic: {data['topic']}")
        print(f"   • Registration URL: {data.get('registration_url', 'N/A')}")
        print(f"   • Join URL: {data['join_url']}")
        print(f"   • Start Time: {data['start_time']}")
    """,
    args=[
        Arg(name="topic", description="Webinar topic/name", required=True),
        Arg(name="start_time", description="Webinar start time (YYYY-MM-DD HH:MM:SS)", required=True),
        Arg(name="duration", description="Webinar duration in minutes", required=False, default="60"),
        Arg(name="timezone", description="Webinar timezone", required=False, default="UTC"),
        Arg(name="host_video", description="Start with host video on", required=False, default="true"),
        Arg(name="panelists_video", description="Start with panelists video on", required=False, default="true"),
        Arg(name="practice_session", description="Enable practice session", required=False, default="true"),
        Arg(name="hd_video", description="Enable HD video", required=False, default="true"),
        Arg(name="approval_type", description="Registration approval type (0=auto, 1=manual)", required=False, default="0"),
        Arg(name="registration_type", description="Registration type (1=required, 2=optional)", required=False, default="1"),
        Arg(name="audio", description="Audio options (both, telephony, voip)", required=False, default="both"),
    ]
)

# Add more webinar tools here
tool_registry.register("zoom", create_webinar_tool) 