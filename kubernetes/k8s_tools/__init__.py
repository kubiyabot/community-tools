# k8s_tools/__init__.py

import logging
import subprocess
import sys
from pathlib import Path
import yaml
import tempfile
import os
from typing import Tuple, Optional
import time
import json
import threading
from .utils.script_runner import run_command

# Configure detailed logging with colors
class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors"""
    grey = "\x1b[38;21m"
    blue = "\x1b[38;5;39m"
    yellow = "\x1b[38;5;226m"
    red = "\x1b[38;5;196m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"

    def __init__(self, fmt):
        super().__init__()
        self.fmt = fmt
        self.FORMATS = {
            logging.DEBUG: self.grey + self.fmt + self.reset,
            logging.INFO: self.blue + self.fmt + self.reset,
            logging.WARNING: self.yellow + self.fmt + self.reset,
            logging.ERROR: self.red + self.fmt + self.reset,
            logging.CRITICAL: self.bold_red + self.fmt + self.reset
        }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)

# Configure logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
formatter = ColoredFormatter('%(asctime)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)

class KubernetesSetupError(Exception):
    """Custom exception for Kubernetes setup errors with troubleshooting steps."""
    def __init__(self, message: str, troubleshooting_steps: list):
        self.message = message
        self.troubleshooting_steps = troubleshooting_steps
        super().__init__(self.format_message())

    def format_message(self) -> str:
        formatted = f"\n{'='*80}\n"
        formatted += f"❌ Error: {self.message}\n\n"
        formatted += "🛠️  Troubleshooting Steps:\n"
        for i, step in enumerate(self.troubleshooting_steps, 1):
            formatted += f"{i}. {step}\n"
        formatted += f"{'='*80}\n"
        return formatted

def validate_prerequisites() -> bool:
    """Validate all prerequisites are installed and configured correctly."""
    logger.info("🔍 Validating prerequisites...")
    
    # Check kubectl
    try:
        version = run_command("kubectl version --client --output=json")
        logger.info(f"✅ kubectl is installed: {json.loads(version)['clientVersion']['gitVersion']}")
    except Exception as e:
        raise KubernetesSetupError(
            "kubectl is not installed or not working properly",
            [
                "Install kubectl:\n   curl -LO https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl",
                "Make kubectl executable:\n   chmod +x kubectl",
                "Move to PATH:\n   sudo mv kubectl /usr/local/bin/",
                "Verify installation:\n   kubectl version --client"
            ]
        )

    # Check helm
    try:
        version = run_command("helm version --short")
        logger.info(f"✅ helm is installed: {version}")
    except Exception as e:
        raise KubernetesSetupError(
            "helm is not installed or not working properly",
            [
                "Install helm:\n   curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash",
                "Verify installation:\n   helm version",
                "Add required repos:\n   helm repo add stable https://charts.helm.sh/stable"
            ]
        )

    # Validate cluster access
    try:
        context = run_command("kubectl config current-context")
        logger.info(f"✅ Connected to cluster: {context}")
    except Exception as e:
        raise KubernetesSetupError(
            "Cannot connect to Kubernetes cluster",
            [
                "Check kubeconfig:\n   kubectl config view",
                "Verify cluster access:\n   kubectl cluster-info",
                "Check credentials:\n   kubectl auth can-i get pods",
                "Verify network connectivity:\n   curl -k https://<cluster-ip>"
            ]
        )

    return True

def verify_namespace_exists(namespace: str = "kubiya") -> bool:
    """Verify namespace exists or create it."""
    try:
        run_command(f"kubectl get namespace {namespace}")
        logger.info(f"✅ Namespace {namespace} exists")
        return True
    except:
        try:
            run_command(f"kubectl create namespace {namespace}")
            logger.info(f"✅ Created namespace {namespace}")
            return True
        except Exception as e:
            raise KubernetesSetupError(
                f"Failed to create namespace {namespace}",
                [
                    "Check permissions:\n   kubectl auth can-i create namespace",
                    f"Try manually:\n   kubectl create namespace {namespace}",
                    "Verify namespace list:\n   kubectl get namespaces"
                ]
            )

def verify_kubewatch_deployment(timeout: int = 300) -> bool:
    """Verify kubewatch deployment is running properly."""
    logger.info("🔍 Verifying kubewatch deployment...")
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        try:
            # Check deployment status
            status = run_command("kubectl get deployment kubewatch -n kubiya -o json")
            deploy = json.loads(status)
            
            available = deploy['status'].get('availableReplicas', 0)
            desired = deploy['status'].get('replicas', 0)
            
            if available == desired and desired > 0:
                logger.info("✅ Kubewatch deployment is ready and running")
                
                # Verify it's actually working by checking logs
                logs = run_command("kubectl logs -l app=kubewatch -n kubiya --tail=1")
                if "watching" in logs.lower():
                    logger.info("✅ Kubewatch is actively monitoring the cluster")
                    return True
                
            logger.info(f"⏳ Waiting for kubewatch deployment ({available}/{desired} ready)...")
            
        except Exception as e:
            logger.warning(f"⚠️  Deployment check failed: {str(e)}")
        
        time.sleep(5)
    
    raise KubernetesSetupError(
        "Kubewatch deployment verification timed out",
        [
            "Check deployment status:\n   kubectl describe deployment kubewatch -n kubiya",
            "View pod logs:\n   kubectl logs -l app=kubewatch -n kubiya",
            "Check events:\n   kubectl get events -n kubiya",
            "Verify resources:\n   kubectl top pods -n kubiya"
        ]
    )

def create_kubewatch_config() -> bool:
    """Create and validate kubewatch ConfigMap from config file."""
    logger.info("🔄 Creating kubewatch configuration...")
    
    try:
        # Load configuration from our config file
        config_path = Path(__file__).parent / 'config' / 'kubewatch.yaml'
        if not config_path.exists():
            raise KubernetesSetupError(
                f"Kubewatch config not found at {config_path}",
                [
                    f"Verify config file exists:\n   ls -l {config_path}",
                    "Create the config file manually:\n   mkdir -p kubernetes/k8s_tools/config",
                    "Copy the default config:\n   cp config/kubewatch.yaml.example config/kubewatch.yaml",
                    "Check file permissions:\n   ls -la config/"
                ]
            )

        # Load and validate YAML
        try:
            with open(config_path) as f:
                kubewatch_config = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise KubernetesSetupError(
                f"Invalid YAML in kubewatch config: {str(e)}",
                [
                    "Check YAML syntax:\n   yamllint config/kubewatch.yaml",
                    "Validate against schema:\n   kubectl create configmap --dry-run=client -o yaml",
                    "Use online YAML validator:\n   http://www.yamllint.com/"
                ]
            )

        # Validate required fields
        required_fields = ['handler', 'resource']
        missing_fields = [field for field in required_fields if field not in kubewatch_config]
        if missing_fields:
            raise KubernetesSetupError(
                f"Missing required fields in kubewatch config: {', '.join(missing_fields)}",
                [
                    "Required fields are:\n   - handler\n   - resource",
                    "Check example config:\n   cat config/kubewatch.yaml.example",
                    "Verify config structure:\n   https://github.com/kubeshark/kubewatch#configuration"
                ]
            )

        # Create ConfigMap manifest
        config_map = {
            "apiVersion": "v1",
            "kind": "ConfigMap",
            "metadata": {
                "name": "kubewatch-config",
                "namespace": "kubiya"
            },
            "data": {
                ".kubewatch.yaml": yaml.dump(kubewatch_config)
            }
        }

        # Create temporary file for the ConfigMap
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as temp_file:
            yaml.dump(config_map, temp_file)
            config_path = temp_file.name

        try:
            # Try to delete existing ConfigMap if it exists
            try:
                run_command("kubectl delete configmap kubewatch-config -n kubiya --ignore-not-found")
                logger.info("🗑️  Cleaned up existing kubewatch config")
            except Exception:
                pass

            # Apply new ConfigMap
            result = run_command(f"kubectl apply -f {config_path}")
            logger.info("✅ Applied kubewatch configuration")

            # Verify ConfigMap was created
            verify_result = run_command("kubectl get configmap kubewatch-config -n kubiya -o name")
            if "configmap/kubewatch-config" in verify_result:
                logger.info("✅ Verified kubewatch ConfigMap exists")
                return True
            else:
                raise Exception("ConfigMap verification failed")

        except Exception as e:
            raise KubernetesSetupError(
                f"Failed to create ConfigMap: {str(e)}",
                [
                    "Check kubectl access:\n   kubectl auth can-i create configmap -n kubiya",
                    "Try manually:\n   kubectl create configmap kubewatch-config --from-file=.kubewatch.yaml=config/kubewatch.yaml -n kubiya",
                    "Verify namespace exists:\n   kubectl get namespace kubiya",
                    "Check events:\n   kubectl get events -n kubiya"
                ]
            )
        finally:
            # Clean up temporary file
            os.unlink(config_path)

    except Exception as e:
        if not isinstance(e, KubernetesSetupError):
            raise KubernetesSetupError(
                f"Failed to create kubewatch config: {str(e)}",
                [
                    "Verify config file exists and is readable",
                    "Check YAML syntax in config file",
                    "Ensure kubectl has necessary permissions",
                    "Verify kubiya namespace exists"
                ]
            )
        raise

    return False

# Initialize with proper validation
try:
    logger.info("🚀 Initializing Kubernetes tools...")
    
    # Validate prerequisites
    validate_prerequisites()
    
    # Verify namespace
    verify_namespace_exists()
    
    # Setup cluster permissions
    if not setup_cluster_permissions():
        raise Exception("Failed to setup cluster permissions")
    logger.info("✅ Cluster permissions configured successfully")

    # Create kubewatch config
    if not create_kubewatch_config():
        raise Exception("Failed to create kubewatch config")
    logger.info("✅ Kubewatch config created successfully")

    # Start background deployment with proper verification
    def deploy_and_verify():
        try:
            if deploy_kubewatch():
                if verify_kubewatch_deployment():
                    logger.info("🎉 Kubewatch deployment completed successfully")
                    return
            raise Exception("Deployment failed")
        except Exception as e:
            logger.error(f"❌ Kubewatch deployment failed: {str(e)}")
    
    setup_thread = threading.Thread(target=deploy_and_verify)
    setup_thread.daemon = True
    setup_thread.start()
    logger.info("✅ Background deployment started")

except KubernetesSetupError as e:
    logger.error(str(e))
    sys.exit(1)
except Exception as e:
    logger.error(f"❌ Unexpected error during initialization: {str(e)}")
    sys.exit(1)

# Import tools after successful initialization
from .tools import *

# Export the initialization functions
__all__ = [
    'deploy_kubewatch',
    'create_kubewatch_config', 
    'setup_cluster_permissions',
    'verify_kubewatch_deployment',
    'KubernetesSetupError'
]