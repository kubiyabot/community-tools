from kubiya_sdk.tools import Tool

ARGOCD_ICON_URL = "https://cncf-branding.netlify.app/img/projects/argo/icon/color/argo-icon-color.png"

class ArgoCDTool(Tool):
    def __init__(self, name, description, content, args, long_running=False):
        super().__init__(
            name=name,
            description=description,
            icon_url=ARGOCD_ICON_URL,
            type="docker",
            image="argoproj/argocd:latest",
            content=content,
            args=args,
            env=["ARGOCD_SERVER", "ARGOCD_AUTH_TOKEN"],
            long_running=long_running
        )