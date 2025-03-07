"""
Zoom Tools Module - Tool Definitions
"""
from kubiya_sdk.tools import Arg
from kubiya_sdk.tools.registry import tool_registry
from .base import ZoomTool

# Meeting Tools
create_meeting_tool = ZoomTool(
    name="create-zoom-meeting",
    description="Create a new Zoom meeting with specified parameters",
    content="python3 /usr/local/lib/zoom_tools/handlers/meeting_handler.py create",
    args=[
        Arg(name="topic", description="Meeting topic/name (e.g., 'Team Standup', 'Project Review')", required=True),
        Arg(name="start_time", description="Meeting start time (YYYY-MM-DD HH:MM:SS)", required=True),
        Arg(name="duration", description="Meeting duration in minutes", required=False, default="60"),
        Arg(name="timezone", description="Meeting timezone (e.g., 'UTC', 'America/New_York')", required=False, default="UTC"),
        Arg(name="password", description="Custom meeting password", required=False),
        Arg(name="host_video", description="Start with host video on (true/false)", required=False, default="true"),
        Arg(name="participant_video", description="Start with participant video on (true/false)", required=False, default="true"),
        Arg(name="join_before_host", description="Allow joining before host (true/false)", required=False, default="false"),
        Arg(name="mute_upon_entry", description="Mute participants upon entry (true/false)", required=False, default="false"),
        Arg(name="waiting_room", description="Enable waiting room (true/false)", required=False, default="true"),
    ]
)

meeting_controls_tool = ZoomTool(
    name="control-zoom-meeting",
    description="Control an ongoing Zoom meeting (mute all, remove participant, etc)",
    content="python3 /usr/local/lib/zoom_tools/handlers/meeting_handler.py control",
    args=[
        Arg(name="meeting_id", description="ID of the meeting to control", required=True),
        Arg(name="action", description="Control action (mute_all, unmute_all, end_meeting, remove_<participant_id>)", required=True),
    ]
)

list_recordings_tool = ZoomTool(
    name="list-zoom-recordings",
    description="List all recordings for a specific date range",
    content="python3 /usr/local/lib/zoom_tools/handlers/meeting_handler.py recordings",
    args=[
        Arg(name="start_date", description="Start date for recordings (YYYY-MM-DD)", required=True),
        Arg(name="end_date", description="End date for recordings (YYYY-MM-DD)", required=False),
    ]
)

# Webinar Tools
create_webinar_tool = ZoomTool(
    name="create-zoom-webinar",
    description="Create a new Zoom webinar",
    content="python3 /usr/local/lib/zoom_tools/handlers/webinar_handler.py create",
    args=[
        Arg(name="topic", description="Webinar topic/name", required=True),
        Arg(name="start_time", description="Webinar start time (YYYY-MM-DD HH:MM:SS)", required=True),
        Arg(name="duration", description="Webinar duration in minutes", required=False, default="60"),
        Arg(name="timezone", description="Webinar timezone", required=False, default="UTC"),
        Arg(name="host_video", description="Start with host video on", required=False, default="true"),
        Arg(name="panelists_video", description="Start with panelists video on", required=False, default="true"),
        Arg(name="practice_session", description="Enable practice session", required=False, default="true"),
        Arg(name="hd_video", description="Enable HD video", required=False, default="true"),
    ]
)

# User Tools
list_users_tool = ZoomTool(
    name="list-zoom-users",
    description="List all users in the Zoom account",
    content="python3 /usr/local/lib/zoom_tools/handlers/user_handler.py list",
    args=[
        Arg(name="status", description="User status to filter by (active, inactive, pending)", required=False, default="active"),
    ]
)

# Register all tools
for tool in [
    create_meeting_tool,
    meeting_controls_tool,
    list_recordings_tool,
    create_webinar_tool,
    list_users_tool
]:
    tool_registry.register("zoom", tool)