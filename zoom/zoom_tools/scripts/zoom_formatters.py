def format_meeting_details(meeting):
    """Format meeting details in nice markdown"""
    join_url = meeting.get('join_url', 'N/A')
    password = meeting.get('password', 'N/A')
    
    return f"""
### 📅 Meeting Created Successfully!

#### Meeting Details
| Field | Value |
|-------|--------|
| Topic | {meeting['topic']} |
| ID | `{meeting['id']}` |
| Status | {meeting.get('status', 'Scheduled')} |
| Start Time | {meeting.get('start_time', 'N/A')} |
| Duration | {meeting.get('duration', 'N/A')} minutes |

#### Quick Access
🔗 **Join URL**: [{join_url}]({join_url})
🔑 **Password**: `{password}`

#### Additional Settings
- Host Video: {'🎥 On' if meeting.get('settings', {}).get('host_video') else '🎥 Off'}
- Participant Video: {'📹 On' if meeting.get('settings', {}).get('participant_video') else '📹 Off'}
- Waiting Room: {'🚪 Enabled' if meeting.get('settings', {}).get('waiting_room') else '🚪 Disabled'}
- Join Before Host: {'✅ Allowed' if meeting.get('settings', {}).get('join_before_host') else '❌ Not Allowed'}
"""

def format_webinar_details(webinar):
    """Format webinar details in nice markdown"""
    join_url = webinar.get('join_url', 'N/A')
    registration_url = webinar.get('registration_url', 'N/A')
    
    return f"""
### 📺 Webinar Created Successfully!

#### Webinar Details
| Field | Value |
|-------|--------|
| Topic | {webinar['topic']} |
| ID | `{webinar['id']}` |
| Status | {webinar.get('status', 'Scheduled')} |
| Start Time | {webinar.get('start_time', 'N/A')} |
| Duration | {webinar.get('duration', 'N/A')} minutes |

#### Access Links
🔗 **Join URL**: [{join_url}]({join_url})
📝 **Registration**: [{registration_url}]({registration_url})

#### Additional Settings
- Host Video: {'🎥 On' if webinar.get('settings', {}).get('host_video') else '🎥 Off'}
- Panelist Video: {'📹 On' if webinar.get('settings', {}).get('panelists_video') else '📹 Off'}
- Practice Session: {'🎯 Enabled' if webinar.get('settings', {}).get('practice_session') else '🎯 Disabled'}
- HD Video: {'📺 Enabled' if webinar.get('settings', {}).get('hd_video') else '📺 Standard'}
"""

def format_recording_details(recordings):
    """Format recording details in nice markdown"""
    if not recordings:
        return "### 📹 No recordings found for the specified period"
        
    output = ["### 📹 Zoom Recordings\n"]
    
    for meeting in recordings:
        output.append(f"#### 📅 {meeting['topic']}")
        output.append(f"**Date**: {meeting['start_time']}")
        output.append(f"**Duration**: {meeting['duration']} minutes\n")
        
        if 'recording_files' in meeting:
            output.append("| Type | Size | Download |")
            output.append("|------|------|----------|")
            for recording in meeting['recording_files']:
                size_mb = recording['file_size'] / 1024 / 1024
                download_url = recording['download_url']
                output.append(
                    f"| {recording['recording_type']} | {size_mb:.1f} MB | "
                    f"[⬇️ Download]({download_url}) |"
                )
        output.append("\n---\n")
    
    return "\n".join(output)

def format_user_list(users):
    """Format user list in nice markdown"""
    if not users:
        return "### 👥 No users found"
        
    output = ["### 👥 Zoom Users\n"]
    output.append("| Name | Email | Type | Status | Created |")
    output.append("|------|--------|------|---------|----------|")
    
    for user in users:
        name = f"{user['first_name']} {user['last_name']}"
        output.append(
            f"| {name} | {user['email']} | {user['type']} | "
            f"{user['status']} | {user['created_at']} |"
        )
    
    return "\n".join(output)

def format_meeting_control_result(action, success=True):
    """Format meeting control results in nice markdown"""
    action_emojis = {
        'mute_all': '🔇',
        'unmute_all': '🔊',
        'end_meeting': '🛑',
        'remove': '⛔'
    }
    
    emoji = next((v for k, v in action_emojis.items() if k in action), '🎮')
    
    if success:
        return f"""
### {emoji} Meeting Control Action Successful

**Action**: `{action}`
**Status**: ✅ Completed
"""
    else:
        return f"""
### {emoji} Meeting Control Action Failed

**Action**: `{action}`
**Status**: ❌ Failed
""" 