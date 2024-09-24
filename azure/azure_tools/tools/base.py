from kubiya_sdk.tools import Tool

AZURE_ICON_URL = "https://azure.microsoft.com/svghandler/azure-logo/?width=300&height=300"

class AzureTool(Tool):
    def __init__(self, name, description, content, args, long_running=False, mermaid_diagram=None):
        super().__init__(
            name=name,
            description=description,
            icon_url=AZURE_ICON_URL,
            type="docker",
            image="mcr.microsoft.com/azure-cli:latest",
            content=content,
            args=args,
            env=["AZURE_SUBSCRIPTION_ID", "AZURE_TENANT_ID", "AZURE_CLIENT_ID", "AZURE_CLIENT_SECRET"],
            long_running=long_running,
            mermaid=mermaid_diagram
        )

def register_azure_tool(tool):
    from kubiya_sdk.tools.registry import tool_registry
    tool_registry.register("azure", tool)