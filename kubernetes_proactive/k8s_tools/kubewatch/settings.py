from dataclasses import dataclass
from typing import Dict, List, Any

@dataclass
class KubeWatchSettings:
    """KubeWatch configuration settings"""
    webhook_url: str = ''
    namespaces: List[str] = None
    watch_settings: Dict[str, bool] = None
    numeric_settings: Dict[str, Any] = None
    advanced_settings: Dict[str, Any] = None

    def __post_init__(self):
        if self.namespaces is None:
            self.namespaces = ['default', 'kube-system']
        if self.watch_settings is None:
            self.watch_settings = {}
        if self.numeric_settings is None:
            self.numeric_settings = {}
        if self.advanced_settings is None:
            self.advanced_settings = {} 