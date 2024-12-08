import logging
import os
from typing import Any, Dict, Optional, List
from kubiya_sdk.tools import Tool, Arg
from kubiya_sdk.tools.models import FileSpec
from .config import DEFAULT_JENKINS_CONFIG
import json
from pathlib import Path

logger = logging.getLogger(__name__)

class JenkinsHousekeepingTool(Tool):
    """Base class for Jenkins housekeeping tools."""
    def __init__(self, **data):
        super().__init__(**data)
        self.jenkins_url = DEFAULT_JENKINS_CONFIG['jenkins_url']
        self.username = DEFAULT_JENKINS_CONFIG['auth']['username']

        # Add environment variables and secrets
        self.env = (self.env or []) + ["JENKINS_URL", "JENKINS_USERNAME"]
        self.secrets = (self.secrets or []) + ["JENKINS_API_TOKEN"]

class DeleteOldBuildsTool(JenkinsHousekeepingTool):
    """Tool to delete old builds from Jenkins jobs."""
    name = "delete_old_builds"
    description = "Delete builds older than a specified number of days from Jenkins jobs."
    args = [
        Arg(
            name="job_name",
            type="str",
            description="Name of the Jenkins job.",
            required=True,
        ),
        Arg(
            name="days",
            type="int",
            description="Number of days; builds older than this will be deleted.",
            required=True,
        ),
    ]

    def prepare(self):
        """Prepare the tool for execution."""
        self.content = "#!/bin/sh\npython3 /opt/scripts/delete_old_builds.py"
        self.with_files = [
            FileSpec(
                destination="/opt/scripts/delete_old_builds.py",
                source=str(Path(__file__).parent.parent / 'scripts' / 'housekeeping' / 'delete_old_builds.py')
            )
        ]

class ManagePluginsTool(JenkinsHousekeepingTool):
    """Tool to list and optionally update Jenkins plugins."""
    name = "manage_plugins"
    description = "List installed Jenkins plugins and optionally update them."
    args = [
        Arg(
            name="action",
            type="str",
            description="Action to perform: 'list', 'update_all', or 'update_plugin'.",
            required=True,
            choices=["list", "update_all", "update_plugin"]
        ),
        Arg(
            name="plugin_name",
            type="str",
            description="Name of the plugin to update (required if action is 'update_plugin').",
            required=False,
        ),
    ]

    def prepare(self):
        """Prepare the tool for execution."""
        self.content = "#!/bin/sh\npython3 /opt/scripts/manage_plugins.py"
        self.with_files = [
            FileSpec(
                destination="/opt/scripts/manage_plugins.py",
                source=str(Path(__file__).parent.parent / 'scripts' / 'housekeeping' / 'manage_plugins.py')
            )
        ]

class ManageNodesTool(JenkinsHousekeepingTool):
    """Tool to manage Jenkins nodes/agents."""
    name = "manage_nodes"
    description = "List and manage Jenkins nodes/agents."
    args = [
        Arg(
            name="action",
            type="str",
            description="Action to perform: 'list' or 'toggle'.",
            required=True,
            choices=["list", "toggle"]
        ),
        Arg(
            name="node_name",
            type="str",
            description="Name of the node (required for toggle action).",
            required=False,
        ),
        Arg(
            name="node_state",
            type="str",
            description="Desired node state: 'online' or 'offline' (required for toggle action).",
            required=False,
            choices=["online", "offline"]
        ),
    ]

    def prepare(self):
        """Prepare the tool for execution."""
        self.content = "#!/bin/sh\npython3 /opt/scripts/manage_nodes.py"
        self.with_files = [
            FileSpec(
                destination="/opt/scripts/manage_nodes.py",
                source=str(Path(__file__).parent.parent / 'scripts' / 'housekeeping' / 'manage_nodes.py')
            )
        ]

class SystemInfoTool(JenkinsHousekeepingTool):
    """Tool to get Jenkins system information and metrics."""
    name = "system_info"
    description = "Get Jenkins system information and metrics."
    args = [
        Arg(
            name="action",
            type="str",
            description="Type of information to retrieve: 'info' or 'metrics'.",
            required=True,
            choices=["info", "metrics"]
        ),
    ]

    def prepare(self):
        """Prepare the tool for execution."""
        self.content = "#!/bin/sh\npython3 /opt/scripts/system_info.py"
        self.with_files = [
            FileSpec(
                destination="/opt/scripts/system_info.py",
                source=str(Path(__file__).parent.parent / 'scripts' / 'housekeeping' / 'system_info.py')
            )
        ]

class JobStatisticsTool(JenkinsHousekeepingTool):
    """Tool to analyze Jenkins job statistics."""
    name = "job_statistics"
    description = "Get statistics and analysis of Jenkins jobs."
    args = [
        Arg(
            name="action",
            type="str",
            description="Type of statistics to retrieve: 'summary' or 'job_stats'.",
            required=True,
            choices=["summary", "job_stats"]
        ),
        Arg(
            name="job_name",
            type="str",
            description="Name of the job to analyze (required for job_stats action).",
            required=False,
        ),
        Arg(
            name="days",
            type="int",
            description="Number of days to analyze (default: 30).",
            required=False,
            default="30"
        ),
    ]

    def prepare(self):
        """Prepare the tool for execution."""
        self.content = "#!/bin/sh\npython3 /opt/scripts/job_statistics.py"
        self.with_files = [
            FileSpec(
                destination="/opt/scripts/job_statistics.py",
                source=str(Path(__file__).parent.parent / 'scripts' / 'housekeeping' / 'job_statistics.py')
            )
        ] 