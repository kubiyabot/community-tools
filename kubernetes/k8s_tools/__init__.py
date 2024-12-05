# k8s_tools/__init__.py

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
    

def create_helm_values() -> Optional[str]:
    """Create custom values.yaml for helm with all required configuration."""
    try:
        # Define helm values
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
                        "url": "${WEBHOOK_URL}"
                    }
                }
            },
            "replicaCount": 1,
            "nodeSelector": {},
            "tolerations": [],
            "affinity": {}
        }

        # Create temporary values file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as temp_file:
            yaml.dump(values, temp_file)
            values_path = temp_file.name
            logger.info(f"✅ Created helm values file at {values_path}")
            return values_path

    except Exception as e:
        troubleshooting = [
            "Manually create values.yaml with the following content:\n" +
            "image:\n" +
            "  repository: ghcr.io/kubiyabot/kubewatch\n" +
            "  tag: dd496405c04f285b3d164f11e4463b3ea02e6ea1\n" +
            "rbac:\n" +
            "  create: true\n" +
            "resourcesToWatch:\n" +
            "  daemonset: true\n" +
            "  pod: true\n" +
            "extraVolumes:\n" +
            "  - name: config-volume\n" +
            "    configMap:\n" +
            "      name: kubewatch-config\n" +
            "extraVolumeMounts:\n" +
            "  - name: config-volume\n" +
            "    mountPath: /root/.kubewatch.yaml\n" +
            "    subPath: .kubewatch.yaml",
            "Verify yaml syntax:\n" +
            "   yamllint values.yaml",
            "Check file permissions:\n" +
            "   ls -la values.yaml"
        ]
        raise KubernetesSetupError(
            f"Failed to create helm values file: {str(e)}",
            troubleshooting
        )

def verify_command_exists(command: str) -> Tuple[bool, str]:
    """Verify if a command exists and return its path."""
    try:
        result = subprocess.run(["which", command], capture_output=True, text=True)
        if result.returncode == 0:
            return True, result.stdout.strip()
        return False, ""
    except Exception:
        return False, ""

def install_prerequisites() -> bool:
    """Install required binaries (kubectl, helm)."""
    try:
        # Check if kubectl exists
        kubectl_exists, kubectl_path = verify_command_exists("kubectl")
        if not kubectl_exists:
            logger.info("🔄 Installing kubectl...")
            kubectl_commands = [
                "curl -LO https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl",
                "chmod +x kubectl",
                "mv kubectl /usr/local/bin/"
            ]
            for cmd in kubectl_commands:
                subprocess.run(cmd, shell=True, check=True)
        
        # Check if helm exists
        helm_exists, helm_path = verify_command_exists("helm")
        if not helm_exists:
            logger.info("🔄 Installing helm...")
            helm_commands = [
                "curl -fsSL -o get_helm.sh https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3",
                "chmod +x get_helm.sh",
                "./get_helm.sh",
                "rm get_helm.sh"
            ]
            for cmd in helm_commands:
                subprocess.run(cmd, shell=True, check=True)

        return True
    except Exception as e:
        troubleshooting = [
            "Manually install kubectl:\n" +
            "   curl -LO https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl\n" +
            "   chmod +x kubectl\n" +
            "   sudo mv kubectl /usr/local/bin/",
            "Manually install helm:\n" +
            "   curl -fsSL -o get_helm.sh https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3\n" +
            "   chmod +x get_helm.sh\n" +
            "   ./get_helm.sh",
            "Verify installations:\n" +
            "   kubectl version\n" +
            "   helm version",
            "Check directory permissions:\n" +
            "   ls -la /usr/local/bin\n" +
            "   sudo chown -R $(whoami) /usr/local/bin"
        ]
        raise KubernetesSetupError(
            f"Failed to install prerequisites: {str(e)}", 
            troubleshooting
        )

def setup_cluster_permissions() -> bool:
    """Setup required cluster permissions."""
    try:
        # Create cluster role binding for kubiya service account
        cmd = [
            "kubectl", "create", "clusterrolebinding", "kubiya-sa-cluster-admin",
            "--clusterrole=cluster-admin",
            "--serviceaccount=kubiya:kubiya-service-account"
        ]
        subprocess.run(cmd, check=True)
        
        # Verify permissions
        cmd = [
            "kubectl", "auth", "can-i", "list", "pods",
            "--as=system:serviceaccount:kubiya:kubiya-service-account",
            "--all-namespaces"
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if "yes" not in result.stdout.lower():
            troubleshooting = [
                "Verify the kubiya namespace exists:\n" +
                "   kubectl get namespace kubiya",
                "Create the namespace if it doesn't exist:\n" +
                "   kubectl create namespace kubiya",
                "Verify the service account exists:\n" +
                "   kubectl get serviceaccount kubiya-service-account -n kubiya",
                "Create the service account if it doesn't exist:\n" +
                "   kubectl create serviceaccount kubiya-service-account -n kubiya",
                "Manually create the cluster role binding:\n" +
                "   kubectl create clusterrolebinding kubiya-sa-cluster-admin \\\n" +
                "   --clusterrole=cluster-admin \\\n" +
                "   --serviceaccount=kubiya:kubiya-service-account",
                "Verify permissions:\n" +
                "   kubectl auth can-i --list --as=system:serviceaccount:kubiya:kubiya-service-account"
            ]
            raise KubernetesSetupError(
                "Service account does not have required permissions",
                troubleshooting
            )
        
        return True
    except subprocess.CalledProcessError as e:
        troubleshooting = [
            "Verify you have cluster-admin permissions:\n" +
            "   kubectl auth can-i create clusterrolebinding",
            "Check if the binding already exists:\n" +
            "   kubectl get clusterrolebinding kubiya-sa-cluster-admin",
            "Delete existing binding if needed:\n" +
            "   kubectl delete clusterrolebinding kubiya-sa-cluster-admin",
            "Verify the kubiya namespace and service account:\n" +
            "   kubectl get namespace kubiya\n" +
            "   kubectl get serviceaccount -n kubiya"
        ]
        raise KubernetesSetupError(
            f"Failed to setup cluster permissions: {e.stderr.decode() if e.stderr else str(e)}",
            troubleshooting
        )

def create_kubewatch_config() -> bool:
    """Create kubewatch ConfigMap."""
    try:
        # Load configuration from our config file
        config_path = Path(__file__).parent / 'config' / 'kubewatch.yaml'
        if not config_path.exists():
            troubleshooting = [
                f"Verify config file exists:\n" +
                f"   ls -l {config_path}",
                "Create the config file manually:\n" +
                "   mkdir -p kubernetes/k8s_tools/config\n" +
                "   vim kubernetes/k8s_tools/config/kubewatch.yaml",
                "Check file permissions:\n" +
                f"   ls -la {config_path.parent}"
            ]
            raise KubernetesSetupError(
                f"Kubewatch config not found at {config_path}",
                troubleshooting
            )

        with open(config_path) as f:
            kubewatch_config = yaml.safe_load(f)

        # Create ConfigMap manifest
        config_map = {
            "apiVersion": "v1",
            "kind": "ConfigMap",
            "metadata": {
                "name": "kubewatch-config",
                "namespace": "default"
            },
            "data": {
                ".kubewatch.yaml": yaml.dump(kubewatch_config)
            }
        }

        # Apply ConfigMap
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as temp_file:
            yaml.dump(config_map, temp_file)
            config_path = temp_file.name

        try:
            subprocess.run(["kubectl", "apply", "-f", config_path], check=True)
        except subprocess.CalledProcessError as e:
            troubleshooting = [
                "Manually create the ConfigMap:\n" +
                "   kubectl create configmap kubewatch-config --from-file=.kubewatch.yaml=config/kubewatch.yaml -n default",
                "Check if ConfigMap already exists:\n" +
                "   kubectl get configmap kubewatch-config -n default",
                "Delete existing ConfigMap if needed:\n" +
                "   kubectl delete configmap kubewatch-config -n default",
                "Verify permissions:\n" +
                "   kubectl auth can-i create configmap -n default"
            ]
            raise KubernetesSetupError(
                f"Failed to create ConfigMap: {e.stderr.decode() if e.stderr else str(e)}",
                troubleshooting
            )
        finally:
            os.unlink(config_path)
        
        return True
    except Exception as e:
        if not isinstance(e, KubernetesSetupError):
            troubleshooting = [
                "Check kubectl configuration:\n" +
                "   kubectl config view",
                "Verify cluster access:\n" +
                "   kubectl cluster-info",
                "Check namespace permissions:\n" +
                "   kubectl auth can-i create configmap -n default"
            ]
            raise KubernetesSetupError(
                f"Failed to create kubewatch config: {str(e)}",
                troubleshooting
            )
        raise

def deploy_kubewatch() -> bool:
    """Deploy kubewatch using helm."""
    try:
        # Add helm repo
        subprocess.run(
            ["helm", "repo", "add", "robusta", "https://robusta-charts.storage.googleapis.com"],
            check=True
        )
        subprocess.run(["helm", "repo", "update"], check=True)

        # Create values file
        values_file = create_helm_values()
        if not values_file:
            troubleshooting = [
                "Manually create values.yaml:\n" +
                "   vim values.yaml  # Copy content from create_helm_values()",
                "Verify file permissions:\n" +
                "   ls -la values.yaml"
            ]
            raise KubernetesSetupError(
                "Failed to create helm values file",
                troubleshooting
            )

        try:
            # Deploy kubewatch
            subprocess.run([
                "helm", "upgrade", "--install", "kubewatch",
                "robusta/kubewatch", "-f", values_file
            ], check=True)
            
            return True
        except subprocess.CalledProcessError as e:
            troubleshooting = [
                "Verify helm installation:\n" +
                "   helm version",
                "Check helm repositories:\n" +
                "   helm repo list\n" +
                "   helm repo update",
                "Manually install kubewatch:\n" +
                "   helm upgrade --install kubewatch robusta/kubewatch -f values.yaml",
                "Check existing installation:\n" +
                "   helm list -A | grep kubewatch",
                "Debug helm installation:\n" +
                "   helm upgrade --install kubewatch robusta/kubewatch -f values.yaml --debug",
                "Verify Tiller permissions (if using Helm 2):\n" +
                "   kubectl get serviceaccount tiller -n kube-system"
            ]
            raise KubernetesSetupError(
                f"Failed to deploy kubewatch (failed to apply helm chart):\n\n" +
                f"{e.stderr.decode() if e.stderr else str(e)}" +
                "\n\n" +
                f"Stdout:\n{e.stdout.decode() if e.stdout else 'No relevant output from helm'}",
                troubleshooting
            )
        finally:
            os.unlink(values_file)

    except Exception as e:
        if not isinstance(e, KubernetesSetupError):
            troubleshooting = [
                "Verify helm and kubectl are installed:\n" +
                "   which helm kubectl",
                "Check cluster access:\n" +
                "   kubectl cluster-info",
                "Verify helm repositories:\n" +
                "   helm repo list"
            ]
            raise KubernetesSetupError(
                f"Failed to deploy kubewatch (failed to install helm chart):\n\n" +
                f"{str(e)}",
                troubleshooting
            )
        raise

def verify_kubewatch_deployment() -> bool:
    """Verify that kubewatch is properly deployed and running."""
    try:
        # Wait for pod to be ready
        max_attempts = 30
        attempt = 0
        while attempt < max_attempts:
            try:
                # Check pod status
                result = subprocess.run(
                    ["kubectl", "get", "pods", "-n", "default", "-l", "app=kubewatch", "-o", "json"],
                    capture_output=True,
                    text=True,
                    check=True
                )
                pods = json.loads(result.stdout)
                
                if not pods.get('items'):
                    logger.info("⏳ Waiting for kubewatch pod to be created...")
                    attempt += 1
                    time.sleep(2)
                    continue

                pod = pods['items'][0]
                status = pod.get('status', {})
                phase = status.get('phase')
                
                if phase == 'Running':
                    conditions = status.get('conditions', [])
                    ready = any(c.get('type') == 'Ready' and c.get('status') == 'True' for c in conditions)
                    if ready:
                        logger.info("✅ Kubewatch pod is running and ready")
                        
                        # Verify ConfigMap is mounted
                        result = subprocess.run(
                            ["kubectl", "exec", pod['metadata']['name'], "--", "cat", "/root/.kubewatch.yaml"],
                            capture_output=True,
                            text=True
                        )
                        if result.returncode == 0:
                            logger.info("✅ Kubewatch config is properly mounted")
                            return True
                        else:
                            logger.error("❌ Kubewatch config mount verification failed")
                            return False
                
                logger.info(f"⏳ Waiting for kubewatch pod to be ready (Status: {phase})")
                attempt += 1
                time.sleep(2)
            
            except subprocess.CalledProcessError as e:
                logger.error(f"Error checking pod status: {e.stderr}")
                attempt += 1
                time.sleep(2)
                
        logger.error("❌ Timeout waiting for kubewatch pod to be ready")
        return False
        
    except Exception as e:
        logger.error(f"❌ Failed to verify kubewatch deployment: {str(e)}")
        return False

def verify_kubewatch_functionality() -> bool:
    """Verify that kubewatch is functioning by creating a test event."""
    try:
        logger.info("🔍 Testing kubewatch functionality...")
        
        # Create a test pod to trigger an event
        test_pod = {
            "apiVersion": "v1",
            "kind": "Pod",
            "metadata": {
                "name": "kubewatch-test",
                "labels": {
                    "app": "kubewatch-test"
                }
            },
            "spec": {
                "containers": [{
                    "name": "test",
                    "image": "busybox",
                    "command": ["sh", "-c", "echo 'test' && sleep 5"]
                }]
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as temp_file:
            yaml.dump(test_pod, temp_file)
            pod_path = temp_file.name
            
        try:
            # Apply the test pod
            subprocess.run(["kubectl", "apply", "-f", pod_path], check=True)
            logger.info("✅ Test pod created successfully")
            
            # Wait for pod completion
            time.sleep(10)
            
            # Check kubewatch logs for the event
            result = subprocess.run(
                ["kubectl", "logs", "-l", "app=kubewatch", "--tail=50"],
                capture_output=True,
                text=True
            )
            
            if "kubewatch-test" in result.stdout:
                logger.info("✅ Kubewatch successfully detected test pod event")
                return True
            else:
                logger.error("❌ Kubewatch did not detect test pod event")
                return False
                
        finally:
            # Cleanup
            subprocess.run(["kubectl", "delete", "pod", "kubewatch-test", "--force"], check=True)
            os.unlink(pod_path)
            
    except Exception as e:
        logger.error(f"❌ Failed to verify kubewatch functionality: {str(e)}")
        return False

# Add verification steps to the initialization
try:
    logger.info("🚀 Initializing Kubernetes tools...")
    
    # Install required binaries
    if not install_prerequisites():
        raise Exception("Failed to install prerequisites")
    logger.info("✅ Prerequisites installed successfully")

    # Setup cluster permissions
    if not setup_cluster_permissions():
        raise Exception("Failed to setup cluster permissions")
    logger.info("✅ Cluster permissions configured successfully")

    # Create kubewatch config
    if not create_kubewatch_config():
        raise Exception("Failed to create kubewatch config")
    logger.info("✅ Kubewatch config created successfully")

    # Deploy kubewatch
    if not deploy_kubewatch():
        raise Exception("Failed to deploy kubewatch")
    logger.info("✅ Kubewatch deployment initiated")

    # Verify deployment
    if not verify_kubewatch_deployment():
        raise Exception("Failed to verify kubewatch deployment")
    logger.info("✅ Kubewatch deployment verified")

    # Verify functionality
    if not verify_kubewatch_functionality():
        raise Exception("Failed to verify kubewatch functionality")
    logger.info("✅ Kubewatch functionality verified")

    logger.info("✅ Kubernetes tools initialized successfully")

except KubernetesSetupError as e:
    logger.error(str(e))
    sys.exit(1)
except Exception as e:
    logger.error(f"❌ Unexpected error during initialization: {str(e)}")
    sys.exit(1)

# Import tools after initialization
from .tools import *

# Export the initialization functions
__all__ = [
    'deploy_kubewatch',
    'create_kubewatch_config',
    'setup_cluster_permissions',
    'verify_kubewatch_deployment',
    'verify_kubewatch_functionality',
    'KubernetesSetupError'
]