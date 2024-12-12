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

class KubeWatchConfig:
    """Builder for KubeWatch configuration"""
    
    DEFAULT_WATCH_SETTINGS = {
        'watch_event': True,
        'watch_node': True,
        'watch_pod': True,
        'watch_deployment': True,
        'watch_service': False,
        'watch_ingress': False,
        'watch_configmap': False,
        'watch_secret': False,
        'watch_job': True,
    }

    DEFAULT_NUMERIC_SETTINGS = {
        'batch_size': 1,
        'batch_interval': '5m',
        'max_wait_time': '10m',
        'min_wait_time': '1m',
        'dedup_window': '15m',
        'max_log_lines': 50,
        'max_events': 10,
    }

    DEFAULT_ADVANCED_SETTINGS = {
        'include_logs': True,
        'include_events': True,
        'include_metrics': True,
        'namespace_isolation': False,
        'min_severity': 'Warning',
        'group_events': True,
    }

    @classmethod
    def parse_config(cls, config: Dict) -> KubeWatchSettings:
        """Parse and validate configuration"""
        if not config:
            raise ValueError("No dynamic configuration provided")
        
        print(f"Starting to parse config: {config}")

        # Parse namespaces
        namespaces = config.get('namespaces', 'default,kube-system')
        namespace_list = [ns.strip() for ns in namespaces.split(',') if ns.strip()]
        if not namespace_list:
            print("No namespaces provided, using default namespaces (default, kube-system)")
            namespace_list = ['default', 'kube-system']

        # Parse settings
        watch_settings = {
            key: str(config.get(key, default)).lower() == 'true'
            for key, default in cls.DEFAULT_WATCH_SETTINGS.items()
        }

        numeric_settings = {
            key: (int(config.get(key, default)) if isinstance(default, int) else str(config.get(key, default)))
            for key, default in cls.DEFAULT_NUMERIC_SETTINGS.items()
        }

        advanced_settings = {
            key: (str(config.get(key, default)).lower() == 'true' if isinstance(default, bool) else config.get(key, default))
            for key, default in cls.DEFAULT_ADVANCED_SETTINGS.items()
        }

        return KubeWatchSettings(
            webhook_url=config.get('webhook_url', ''),
            namespaces=namespace_list,
            watch_settings=watch_settings,
            numeric_settings=numeric_settings,
            advanced_settings=advanced_settings
        ) 