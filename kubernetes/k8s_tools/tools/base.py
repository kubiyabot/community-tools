# k8s_tools/tools/base.py

from kubiya_sdk.tools import Tool
from .common import COMMON_ENV, COMMON_FILES

class KubernetesTool(Tool):
    def __init__(self, name, description, content, args, image="bitnami/kubectl:latest"):
        super().__init__(
            name=name,
            description=description,
            type="container",
            image=image,
            content=content,
            args=args,
            env=COMMON_ENV,
            files=COMMON_FILES,
        )
