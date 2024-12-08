from typing import Dict, Any

# Default Jenkins settings for in-cluster access
DEFAULT_JENKINS_CONFIG: Dict[str, Any] = {
    "jenkins_url": "http://jenkins.jenkins.svc.cluster.local:8080",
    "auth": {
        "username": "admin",
        "password_env": "JENKINS_API_TOKEN"
    },
    "jobs": {
        "sync_all": True  # By default, sync all jobs
    },
    "defaults": {
        "stream_logs": True,
        "poll_interval": 30,
        "long_running_threshold": 300
    }
} 