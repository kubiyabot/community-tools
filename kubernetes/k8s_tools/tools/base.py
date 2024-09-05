# k8s_tools/tools/base.py

from kubiya_sdk.tools import Tool
from .common import COMMON_ENV, COMMON_FILES

class KubernetesTool(Tool):
    def __init__(self, name, description, content, args):
        super().__init__(
            name=name,
            description=description,
            type="container",
            image="bitnami/kubectl:latest",
            content=content,
            args=args,
            env=COMMON_ENV,
            files=COMMON_FILES,
        )
