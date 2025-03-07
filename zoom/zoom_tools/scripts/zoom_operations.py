import os
from datetime import datetime
from .zoom_helpers import get_zoom_client, handle_zoom_response, validate_date
from .zoom_formatters import (
    format_meeting_details, 
    format_webinar_details, 
    format_recording_details,
    format_user_list,
    format_meeting_control_result
)

def create_meeting(settings):
    """Create a new Zoom meeting"""
    print("### 🎥 Creating New Zoom Meeting")
    print("*Please wait while we set up your meeting...*\n")
    
    client = get_zoom_client()
    
    meeting_settings = {
        "topic": settings.get('topic', 'Scheduled Meeting'),
        "type": 2,  # Scheduled meeting
        "start_time": settings.get('start_time'),
        "duration": int(settings.get('duration', 60)),
        "timezone": settings.get('timezone', 'UTC'),
        "password": settings.get('password', ''),
        "settings": {
            "host_video": settings.get('host_video', 'true').lower() == 'true',
            "participant_video": settings.get('participant_video', 'true').lower() == 'true',
            "join_before_host": settings.get('join_before_host', 'false').lower() == 'true',
            "mute_upon_entry": settings.get('mute_upon_entry', 'false').lower() == 'true',
            "waiting_room": settings.get('waiting_room', 'true').lower() == 'true'
        }
    }
    
    response = client.meeting.create(user_id='me', **meeting_settings)
    data = handle_zoom_response(response, "Meeting created successfully! 🎉")
    
    return format_meeting_details(data)

def control_meeting(meeting_id, action):
    """Control an ongoing Zoom meeting"""
    print(f"### 🎮 Executing Meeting Control")
    print(f"**Action**: `{action}`")
    print("*Processing your request...*\n")
    
    client = get_zoom_client()
    
    try:
        if action == "mute_all":
            response = client.meeting.update(
                meeting_id=meeting_id,
                settings={"mute_upon_entry": True}
            )
            result = format_meeting_control_result('mute_all')
            
        elif action == "unmute_all":
            response = client.meeting.update(
                meeting_id=meeting_id,
                settings={"mute_upon_entry": False}
            )
            result = format_meeting_control_result('unmute_all')
            
        elif action == "end_meeting":
            response = client.meeting.end(meeting_id=meeting_id)
            result = format_meeting_control_result('end_meeting')
            
        elif action.startswith("remove_"):
            participant_id = action.split("_")[1]
            response = client.meeting.participant_remove(
                meeting_id=meeting_id,
                participant_id=participant_id
            )
            result = format_meeting_control_result('remove')
        
        handle_zoom_response(response, "Control action executed successfully")
        return result
        
    except Exception as e:
        error_result = format_meeting_control_result(action, success=False)
        return f"{error_result}\n**Error Details**: {str(e)}"

def list_recordings(start_date, end_date=None):
    """List Zoom recordings for a date range"""
    if not end_date:
        end_date = datetime.now().strftime('%Y-%m-%d')
    
    # Validate dates
    validate_date(start_date)
    validate_date(end_date)
    
    print(f"### 📹 Fetching Zoom Recordings")
    print(f"**Period**: `{start_date}` to `{end_date}`")
    print("*Please wait while we retrieve your recordings...*\n")
    
    client = get_zoom_client()
    response = client.recording.list(
        user_id='me',
        start=start_date,
        end=end_date
    )
    
    data = handle_zoom_response(response, "Recordings retrieved successfully")
    return format_recording_details(data.get('meetings', []))

def create_webinar(settings):
    """Create a new Zoom webinar"""
    print("### 📺 Creating New Zoom Webinar")
    print("*Please wait while we set up your webinar...*\n")
    
    client = get_zoom_client()
    
    webinar_settings = {
        "topic": settings['topic'],
        "type": 5,  # Scheduled webinar
        "start_time": settings['start_time'],
        "duration": int(settings.get('duration', 60)),
        "timezone": settings.get('timezone', 'UTC'),
        "settings": {
            "host_video": settings.get('host_video', 'true').lower() == 'true',
            "panelists_video": settings.get('panelists_video', 'true').lower() == 'true',
            "practice_session": settings.get('practice_session', 'true').lower() == 'true',
            "hd_video": settings.get('hd_video', 'true').lower() == 'true',
            "approval_type": int(settings.get('approval_type', 0)),
            "registration_type": int(settings.get('registration_type', 1)),
            "audio": settings.get('audio', 'both')
        }
    }
    
    response = client.webinar.create(user_id='me', **webinar_settings)
    data = handle_zoom_response(response, "Webinar created successfully! 🎉")
    
    return format_webinar_details(data)

def list_users(status='active'):
    """List Zoom users with specified status"""
    print(f"### 👥 Fetching Zoom Users")
    print(f"**Status Filter**: `{status}`")
    print("*Please wait while we retrieve user information...*\n")
    
    client = get_zoom_client()
    response = client.user.list(status=status)
    data = handle_zoom_response(response, "Users retrieved successfully")
    
    return format_user_list(data.get('users', [])) 