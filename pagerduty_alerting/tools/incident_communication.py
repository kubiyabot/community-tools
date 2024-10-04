from pagerduty_alerting.tools.base import PagerDutyDockerTool
from kubiya_sdk.tools import Arg

class TriggerMajorIncident(PagerDutyDockerTool):
    def __init__(self):
        super().__init__(
            name="trigger_major_incident_communication",
            description="""
Creates a major incident in PagerDuty, generates a Teams bridge link, creates a FreshService ticket,
sends a SEV1 message in the specified Slack channel, and provides all necessary details.
""",
            content=self.get_script(),
            args=[
                Arg(name="description", type="str", description="Full description of the incident.", required=True),
                Arg(name="business_impact", type="str", description="Full description of the business impact.", required=True),
            ],
            env=self.get_env(),
        )

    @staticmethod
    def get_env():
        return PagerDutyDockerTool.get_common_env()

    @staticmethod
    def get_script():
        return PagerDutyDockerTool.get_common_script()

# Register the tool
trigger_major_incident = TriggerMajorIncident()
trigger_major_incident.register("pagerduty")