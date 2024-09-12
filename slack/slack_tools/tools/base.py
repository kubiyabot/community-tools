from kubiya_sdk.tools import Tool

SLACK_ICON_URL = "https://a.slack-edge.com/80588/marketing/img/icons/icon_slack_hash_colored.png"

class SlackTool(Tool):
    def __init__(self, name, description, content, args, long_running=False, thread_context=False):
        env = ["SLACK_API_KEY"]
        if thread_context:
            env.extend(["SLACK_THREAD_TS", "SLACK_CHANNEL_ID"])

        super().__init__(
            name=name,
            description=description,
            icon_url=SLACK_ICON_URL,
            type="python",
            content=content,
            args=args,
            env=env,
            long_running=long_running,
            requirements=["slack_sdk"]
        )