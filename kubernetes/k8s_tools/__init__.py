import logging
import subprocess
import sys
from pathlib import Path
import yaml
import tempfile
import os
from kubernetes import client, config
from typing import Tuple, Optional
import time
import json

# Configure detailed logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class KubernetesSetupError(Exception):
    """Custom exception for Kubernetes setup errors with troubleshooting steps."""
    def __init__(self, message: str, troubleshooting_steps: list):
        self.message = message
        self.troubleshooting_steps = troubleshooting_steps
        super().__init__(self.format_message())

    def format_message(self) -> str:
        formatted = f"\n❌ Error: {self.message}\n\n"
        formatted += "🛠️ Manual Troubleshooting Steps:\n"
        for i, step in enumerate(self.troubleshooting_steps, 1):
            formatted += f"{i}. {step}\n"
        return formatted

def initialize_kubernetes_tools():
    """Initialize Kubernetes tools with proper in-cluster context."""
    try:
        logger.info("🚀 Loading Kubernetes cluster configuration...")

        # Use in-cluster config if running inside a cluster
        try:
            config.load_incluster_config()
            logger.info("✅ Loaded in-cluster Kubernetes configuration")
        except config.ConfigException:
            # Fallback to local kubeconfig for testing outside cluster
            config.load_kube_config()
            logger.info("✅ Loaded kubeconfig from local environment")

        # Verify Kubernetes API connectivity
        api = client.CoreV1Api()
        namespaces = api.list_namespace()
        logger.info("✅ Kubernetes API is reachable. Namespaces available: %s",
                    [ns.metadata.name for ns in namespaces.items])

    except Exception as e:
        troubleshooting = [
            "Verify you are running the script inside a Kubernetes cluster or set up kubeconfig correctly.",
            "Check Kubernetes API server availability:\n"
            "   kubectl cluster-info",
            "Ensure the service account in the cluster has sufficient permissions."
        ]
        raise KubernetesSetupError(f"Failed to initialize Kubernetes tools: {str(e)}", troubleshooting)

def create_helm_values() -> Optional[str]:
    """Create custom values.yaml for helm with all required configuration."""
    try:
        values = {
            "image": {
                "repository": "ghcr.io/kubiyabot/kubewatch",
                "tag": "dd496405c04f285b3d164f11e4463b3ea02e6ea1",
                "pullPolicy": "Always"
            },
            "rbac": {
                "create": True,
                "serviceAccount": {
                    "create": True,
                    "name": "kubewatch"
                }
            },
            "resourcesToWatch": {
                "deployment": True,
                "pod": True,
                "daemonset": True,
                "service": True,
                "configmap": True,
                "namespace": True,
                "job": True,
                "persistentvolume": True,
                "secret": False,
                "ingress": True
            },
            "extraVolumes": [
                {
                    "name": "config-volume",
                    "configMap": {
                        "name": "kubewatch-config"
                    }
                }
            ],
            "extraVolumeMounts": [
                {
                    "name": "config-volume",
                    "mountPath": "/root/.kubewatch.yaml",
                    "subPath": ".kubewatch.yaml"
                }
            ],
            "resources": {
                "limits": {
                    "cpu": "100m",
                    "memory": "128Mi"
                },
                "requests": {
                    "cpu": "50m",
                    "memory": "64Mi"
                }
            },
            "config": {
                "handler": {
                    "webhook": {
                        "enabled": True,
                        "url": os.getenv("WEBHOOK_URL", "")
                    }
                }
            },
            "replicaCount": 1,
            "nodeSelector": {},
            "tolerations": [],
            "affinity": {}
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as temp_file:
            yaml.dump(values, temp_file)
            values_path = temp_file.name
            logger.info(f"✅ Created helm values file at {values_path}")
            return values_path

    except Exception as e:
        troubleshooting = [
            "Verify your helm values.yaml syntax is correct:\n"
            "   yamllint values.yaml",
            "Manually create a values.yaml file and specify the configuration."
        ]
        raise KubernetesSetupError(
            f"Failed to create helm values file: {str(e)}", troubleshooting
        )

def install_prerequisites() -> bool:
    """Install required binaries (kubectl, helm)."""
    try:
        def check_and_install(command: str, install_commands: list):
            exists, _ = verify_command_exists(command)
            if not exists:
                for cmd in install_commands:
                    subprocess.run(cmd, shell=True, check=True)

        # Install kubectl
        check_and_install("kubectl", [
            "curl -LO https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl",
            "chmod +x kubectl",
            "mv kubectl /usr/local/bin/"
        ])

        # Install helm
        check_and_install("helm", [
            "curl -fsSL -o get_helm.sh https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3",
            "chmod +x get_helm.sh",
            "./get_helm.sh",
            "rm get_helm.sh"
        ])

        logger.info("✅ Prerequisites installed successfully")
        return True

    except Exception as e:
        troubleshooting = [
            "Ensure curl is installed on your system.",
            "Manually install kubectl and helm if the script fails."
        ]
        raise KubernetesSetupError(f"Failed to install prerequisites: {str(e)}", troubleshooting)

def verify_command_exists(command: str) -> Tuple[bool, str]:
    """Verify if a command exists and return its path."""
    try:
        result = subprocess.run(["which", command], capture_output=True, text=True)
        if result.returncode == 0:
            return True, result.stdout.strip()
        return False, ""
    except Exception:
        return False, ""

def setup_cluster_permissions() -> bool:
    """Setup required cluster permissions."""
    try:
        cmd = [
            "kubectl", "create", "clusterrolebinding", "kubiya-sa-cluster-admin",
            "--clusterrole=cluster-admin",
            "--serviceaccount=kubiya:kubiya-service-account"
        ]
        subprocess.run(cmd, check=True)
        logger.info("✅ Cluster permissions configured successfully")
        return True
    except subprocess.CalledProcessError as e:
        troubleshooting = [
            "Verify the cluster role binding exists or create it manually.",
            "Ensure your service account has sufficient permissions."
        ]
        raise KubernetesSetupError(f"Failed to setup cluster permissions: {str(e)}", troubleshooting)

def deploy_kubewatch() -> bool:
    """Deploy kubewatch using helm."""
    try:
        subprocess.run(["helm", "repo", "add", "robusta", "https://robusta-charts.storage.googleapis.com"], check=True)
        subprocess.run(["helm", "repo", "update"], check=True)
        values_file = create_helm_values()
        subprocess.run([
            "helm", "upgrade", "--install", "kubewatch",
            "robusta/kubewatch", "-f", values_file
        ], check=True)
        logger.info("✅ Kubewatch deployed successfully")
        os.unlink(values_file)
        return True
    except Exception as e:
        troubleshooting = [
            "Ensure the helm chart is accessible and repositories are updated.",
            "Verify that kubectl and helm are working correctly."
        ]
        raise KubernetesSetupError(f"Failed to deploy kubewatch: {str(e)}", troubleshooting)

try:
    initialize_kubernetes_tools()
    install_prerequisites()
    setup_cluster_permissions()
    deploy_kubewatch()
    logger.info("✅ Kubernetes tools initialized and kubewatch deployed successfully")
except KubernetesSetupError as e:
    logger.error(str(e))
    sys.exit(1)
except Exception as e:
    logger.error(f"❌ Unexpected error: {str(e)}")
    sys.exit(1)
