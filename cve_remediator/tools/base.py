from typing import Optional, List
from kubiya_sdk.tools.models import Arg, Tool
from pydantic import HttpUrl

NVD_LOGO = HttpUrl(
    "https://nvd.nist.gov/App_Themes/Default/Images/favicon-32x32.png"
)

class BaseCVETool(Tool):
    def __init__(
        self,
        name: str,
        description: str,
        content: str,
        args: list[Arg] = [],
        env: list[str] = [],
        secrets: list[str] = [],
        long_running=False,
    ):
        # Wrap the content with common CVE functionality
        content = f"""
import requests
import json
import os
import sys
from typing import List, Dict, Optional

class BaseNVDAPI:
    def __init__(self):
        self.base_url = "https://services.nvd.nist.gov/rest/json/cves/2.0"
        self.headers = {{'Accept': 'application/json'}}

    def make_request(self, params: Dict) -> Dict:
        try:
            response = requests.get(
                self.base_url,
                headers=self.headers,
                params=params
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {{"error": str(e)}}

# Execute the actual command
{{
{content}
}}
"""

        super().__init__(
            name=name,
            description=description,
            icon_url=NVD_LOGO,
            type="python",
            content=content,
            args=args,
            env=env,
            secrets=secrets,
            long_running=long_running,
        )
