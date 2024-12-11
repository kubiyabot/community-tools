from typing import Dict
from .settings import KubeWatchSettings
from .templates import KubeWatchTemplates

class KubeWatchConfigBuilder:
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
        'batch_size': 5,
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
        
        # print the config
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

    @classmethod
    def generate_config(cls, settings: KubeWatchSettings) -> Dict:
        """Generate KubeWatch configuration"""
        config = {
            'version': '1',
            'filter': {
                'watch_for': [],
                'settings': {
                    'dedup_interval': settings.numeric_settings['dedup_window'],
                    'include_labels': True,
                    'namespace_isolation': settings.advanced_settings['namespace_isolation'],
                    'group_by': ['owner', 'app_label'],
                    'log_tail': settings.numeric_settings['max_log_lines']
                }
            },
            'handler': {
                'webhook': {
                    'url': settings.webhook_url,
                    'batchSize': settings.numeric_settings['batch_size'],
                    'maxWaitTime': settings.numeric_settings['max_wait_time'],
                    'minWaitTime': settings.numeric_settings['min_wait_time'],
                    'groupEvents': settings.advanced_settings['group_events'],
                    'groupBy': ['kind', 'namespace', 'reason', 'owner'],
                    'filtering': {
                        'includeRoutineEvents': False,
                        'minSeverity': settings.advanced_settings['min_severity'],
                        'deduplication': {
                            'enabled': True,
                            'window': settings.numeric_settings['dedup_window']
                        }
                    }
                }
            },
            'resource': {
                'pod': settings.watch_settings['watch_pod'],
                'node': settings.watch_settings['watch_node'],
                'deployment': settings.watch_settings['watch_deployment'],
                'service': settings.watch_settings['watch_service'],
                'ingress': settings.watch_settings['watch_ingress'],
                'event': settings.watch_settings['watch_event']
            },
            'enrichment': {
                'include_logs': settings.advanced_settings['include_logs'],
                'include_events': settings.advanced_settings['include_events'],
                'include_metrics': settings.advanced_settings['include_metrics'],
                'max_log_lines': settings.numeric_settings['max_log_lines'],
                'max_events': settings.numeric_settings['max_events']
            }
        }

        # Add watch configurations
        if settings.watch_settings['watch_pod']:
            config['filter']['watch_for'].append(cls._get_pod_watch_config())
        if settings.watch_settings['watch_node']:
            config['filter']['watch_for'].append(cls._get_node_watch_config())

        return config

    @classmethod
    def _get_pod_watch_config(cls) -> Dict:
        """Get Pod watch configuration"""
        return {
            'kind': 'Pod',
            'reasons': [
                '*CrashLoopBackOff*',
                '*OOMKilled*',
                '*ImagePullBackOff*',
                '*RunContainerError*',
                '*Failed*'
            ],
            'severity': 'critical',
            'prompt': KubeWatchTemplates.get_pod_prompt()
        }

    @classmethod
    def _get_node_watch_config(cls) -> Dict:
        """Get Node watch configuration"""
        return {
            'kind': 'Node',
            'reasons': [
                '*NotReady*',
                '*DiskPressure*',
                '*MemoryPressure*',
                '*NetworkUnavailable*'
            ],
            'severity': 'critical',
            'prompt': KubeWatchTemplates.get_node_prompt()
        } 