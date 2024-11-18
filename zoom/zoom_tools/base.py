from kubiya_sdk.tools import Tool

ZOOM_ICON_URL = "https://w7.pngwing.com/pngs/1023/88/png-transparent-zoom-social-media-meeting-logo-apps-social-media-icon-thumbnail.png"

class ZoomTool(Tool):
    def __init__(
        self,
        name,
        description,
        content,
        args=[],
        env=[],
        secrets=["ZOOM_API_KEY", "ZOOM_API_SECRET"],
        long_running=False,
        with_files=None,
        image="python:3.9-alpine",
        mermaid=None
    ):
        # Add common setup for all Zoom tools
        setup_script = """
        #!/bin/sh
        set -e

        # Install required packages
        apk add --no-cache curl jq >/dev/null 2>&1

        # Install Python packages
        pip install --quiet zoomus requests
        """
        
        full_content = setup_script + "\n" + content

        super().__init__(
            name=name,
            description=description,
            icon_url=ZOOM_ICON_URL,
            type="docker",
            image=image,
            content=full_content,
            args=args,
            env=env,
            secrets=secrets,
            long_running=long_running,
            with_files=with_files,
            mermaid=mermaid
        ) 
