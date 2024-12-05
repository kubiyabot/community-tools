import subprocess
import shlex
import os
import logging
import json
import time
import sys
import requests
from pathlib import Path
from typing import List, Dict, Any, Tuple
from collections import defaultdict
from io import StringIO

# Configure detailed logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class VerificationReport:
    """Class to capture and format verification reports."""
    def __init__(self):
        self.buffer = StringIO()
        self.has_errors = False
        self.has_warnings = False

    def add_section(self, title: str, char: str = "="):
        """Add a section header to the report."""
        self.buffer.write(f"\n{char*80}\n")
        self.buffer.write(f"{title}\n")
        self.buffer.write(f"{char*80}\n")

    def add_error(self, error_msg: str):
        """Add an error message to the report."""
        self.has_errors = True
        self.buffer.write(f"\n❌ {error_msg}\n")

    def add_warning(self, warning_msg: str):
        """Add a warning message to the report."""
        self.has_warnings = True
        self.buffer.write(f"\n⚠️  {warning_msg}\n")

    def add_success(self, success_msg: str):
        """Add a success message to the report."""
        self.buffer.write(f"\n✅ {success_msg}\n")

    def get_report(self) -> str:
        """Get the complete report as a string."""
        return self.buffer.getvalue()

class KubernetesVerificationError(Exception):
    """Custom exception that includes the verification report."""
    def __init__(self, message: str, report: str):
        self.message = message
        self.report = report
        super().__init__(self.format_message())

    def format_message(self) -> str:
        return f"""
{'='*80}
❌ Kubernetes Tools Verification Failed
{'='*80}

{self.message}

 Verification Report:
{self.report}

{'='*80}
"""

class KubewatchDeployer:
    def __init__(self, logger):
        self.logger = logger

    def setup_service_account(self) -> bool:
        """Setup required service account and permissions."""
        try:
            # Create namespace if it doesn't exist
            subprocess.run([
                "kubectl", "create", "namespace", "kubiya",
                "--dry-run=client", "-o", "yaml"
            ], check=True)

            # Create service account binding
            self.logger.info("🔄 Setting up kubiya service account permissions...")
            subprocess.run([
                "kubectl", "create", "clusterrolebinding", "kubiya-sa-cluster-admin",
                "--clusterrole=cluster-admin",
                "--serviceaccount=kubiya:kubiya-service-account"
            ], check=True)

            # Verify permissions
            result = subprocess.run([
                "kubectl", "auth", "can-i", "list", "pods",
                "--as=system:serviceaccount:kubiya:kubiya-service-account",
                "--all-namespaces"
            ], capture_output=True, text=True, check=True)

            if "yes" not in result.stdout.lower():
                raise Exception("Service account does not have required permissions")

            self.logger.info("✅ Service account permissions verified")
            return True

        except Exception as e:
            self.logger.error(f"❌ Failed to setup service account: {str(e)}")
            return False

    def create_kubewatch_config(self) -> bool:
        """Create or update kubewatch ConfigMap."""
        try:
            self.logger.info("🔄 Creating kubewatch ConfigMap...")
            
            # Load config from file
            config_path = Path(__file__).parent.parent / 'config' / 'kubewatch.yaml'
            if not config_path.exists():
                raise FileNotFoundError(f"Kubewatch config not found at {config_path}")

            with open(config_path) as f:
                config_content = f.read()

            # Create ConfigMap
            config_cmd = [
                "kubectl", "apply", "-f", "-"
            ]

            config_yaml = f"""
apiVersion: v1
kind: ConfigMap
metadata:
  name: kubewatch-config
  namespace: default
data:
  .kubewatch.yaml: |
{config_content}
"""
            self.logger.info("📝 Applying kubewatch configuration...")
            process = subprocess.Popen(
                config_cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            stdout, stderr = process.communicate(input=config_yaml)

            if process.returncode != 0:
                raise Exception(f"Failed to create ConfigMap: {stderr}")

            self.logger.info("✅ Kubewatch ConfigMap created successfully")
            return True

        except Exception as e:
            self.logger.error(f"❌ Failed to create kubewatch config: {str(e)}")
            return False

    def create_helm_values(self) -> Optional[str]:
        """Create helm values file."""
        try:
            values = {
                "image": {
                    "repository": "ghcr.io/kubiyabot/kubewatch",
                    "tag": "dd496405c04f285b3d164f11e4463b3ea02e6ea1"
                },
                "rbac": {
                    "create": True
                },
                "resourcesToWatch": {
                    "daemonset": True,
                    "pod": True
                },
                "extraVolumes": [{
                    "name": "config-volume",
                    "configMap": {
                        "name": "kubewatch-config"
                    }
                }],
                "extraVolumeMounts": [{
                    "name": "config-volume",
                    "mountPath": "/root/.kubewatch.yaml",
                    "subPath": ".kubewatch.yaml"
                }]
            }

            # Create temporary values file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as temp_file:
                json.dump(values, temp_file, indent=2)
                return temp_file.name

        except Exception as e:
            self.logger.error(f"❌ Failed to create helm values: {str(e)}")
            return None

    def deploy_kubewatch(self) -> bool:
        """Deploy kubewatch using helm."""
        try:
            # Add helm repository
            self.logger.info("🔄 Adding helm repository...")
            subprocess.run(
                ["helm", "repo", "add", "robusta", "https://robusta-charts.storage.googleapis.com"],
                check=True
            )
            subprocess.run(["helm", "repo", "update"], check=True)

            # Create values file
            values_file = self.create_helm_values()
            if not values_file:
                raise Exception("Failed to create helm values file")

            try:
                # Deploy kubewatch
                self.logger.info("🚀 Deploying kubewatch...")
                subprocess.run([
                    "helm", "upgrade", "--install", "kubewatch",
                    "robusta/kubewatch", "-f", values_file
                ], check=True)
                
                self.logger.info("✅ Kubewatch deployed successfully")
                return True

            finally:
                # Cleanup values file
                if values_file:
                    os.unlink(values_file)

        except Exception as e:
            self.logger.error(f"❌ Failed to deploy kubewatch: {str(e)}")
            return False

    def deploy(self) -> bool:
        """Run the complete deployment process."""
        steps = [
            (self.setup_service_account, "Setting up service account"),
            (self.create_kubewatch_config, "Creating kubewatch config"),
            (self.deploy_kubewatch, "Deploying kubewatch")
        ]

        for step_func, step_name in steps:
            self.logger.info(f"\n{'='*80}\n🔄 {step_name}...\n{'='*80}")
            if not step_func():
                self.logger.error(f"❌ Failed at step: {step_name}")
                return False
            self.logger.info(f"✅ Completed: {step_name}")

        self.logger.info("\n✨ Kubewatch deployment completed successfully!")
        return True

class RuntimeVerifier:
    def __init__(self):
        self.report = VerificationReport()
        self.errors = defaultdict(list)
        self.warnings = defaultdict(list)
        self.kubewatch_deployer = KubewatchDeployer(logger)

    def download_binary(self, binary: str) -> bool:
        """Download and install a binary."""
        try:
            if binary == 'kubectl':
                # Get latest stable version
                version_url = "https://dl.k8s.io/release/stable.txt"
                version = requests.get(version_url).text.strip()
                
                # Download kubectl
                download_url = f"https://dl.k8s.io/release/{version}/bin/linux/amd64/kubectl"
                binary_path = "/usr/local/bin/kubectl"
                
                logger.info(f"Downloading kubectl from {download_url}")
                response = requests.get(download_url)
                response.raise_for_status()  # Raise error for bad status codes
                
                # Ensure directory exists
                os.makedirs("/usr/local/bin", exist_ok=True)
                
                with open(binary_path, 'wb') as f:
                    f.write(response.content)
                
                # Make executable
                os.chmod(binary_path, 0o755)
                logger.info("✅ kubectl installed successfully")
                return True
                
            elif binary == 'helm':
                try:
                    # First try using package manager
                    logger.info("Attempting to install helm via package manager...")
                    subprocess.run(["apt-get", "update"], check=True)
                    subprocess.run(["apt-get", "install", "-y", "apt-transport-https"], check=True)
                    
                    # Add helm repository
                    subprocess.run([
                        "curl", "https://baltocdn.com/helm/signing.asc", 
                        "|", "gpg", "--dearmor", 
                        "|", "tee", "/usr/share/keyrings/helm.gpg", ">/dev/null"
                    ], shell=True, check=True)
                    
                    # Add helm repository
                    with open("/etc/apt/sources.list.d/helm-stable-debian.list", "w") as f:
                        f.write("deb [arch=amd64 signed-by=/usr/share/keyrings/helm.gpg] https://baltocdn.com/helm/stable/debian/ all main\n")
                    
                    subprocess.run(["apt-get", "update"], check=True)
                    subprocess.run(["apt-get", "install", "-y", "helm"], check=True)
                    
                    logger.info("✅ Helm installed successfully via package manager")
                    return True
                    
                except Exception as e:
                    logger.warning(f"Failed to install helm via package manager: {str(e)}")
                    logger.info("Attempting alternative helm installation method...")
                    
                    # Alternative method: Direct binary download
                    # Get latest version
                    version_url = "https://get.helm.sh/helm-v3.12.3-linux-amd64.tar.gz"
                    temp_dir = "/tmp/helm-install"
                    os.makedirs(temp_dir, exist_ok=True)
                    
                    # Download and extract
                    logger.info(f"Downloading helm from {version_url}")
                    response = requests.get(version_url)
                    response.raise_for_status()
                    
                    tar_path = f"{temp_dir}/helm.tar.gz"
                    with open(tar_path, 'wb') as f:
                        f.write(response.content)
                    
                    # Extract
                    subprocess.run(["tar", "-zxvf", tar_path, "-C", temp_dir], check=True)
                    
                    # Move binary
                    os.makedirs("/usr/local/bin", exist_ok=True)
                    subprocess.run(["mv", f"{temp_dir}/linux-amd64/helm", "/usr/local/bin/"], check=True)
                    
                    # Cleanup
                    subprocess.run(["rm", "-rf", temp_dir], check=True)
                    
                    logger.info("✅ Helm installed successfully via direct download")
                    return True
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error while downloading {binary}: {str(e)}")
            return False
        except subprocess.CalledProcessError as e:
            logger.error(f"Command failed while installing {binary}: {str(e)}")
            return False
        except PermissionError as e:
            logger.error(f"Permission error while installing {binary}. Try running with sudo: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error while installing {binary}: {str(e)}")
            return False
            
        return False

    def verify_binary_installation(self) -> bool:
        """Verify that required binaries are installed and accessible."""
        self.report.add_section("Binary Dependencies")
        success = True
        binaries = {
            'kubectl': {
                'version_cmd': ['kubectl', 'version', '--client'],
                'install_guide': "https://kubernetes.io/docs/tasks/tools/install-kubectl/"
            },
            'helm': {
                'version_cmd': ['helm', 'version'],
                'install_guide': "https://helm.sh/docs/intro/install/"
            }
        }

        for binary, info in binaries.items():
            try:
                location = subprocess.run(['which', binary], capture_output=True, text=True)
                if location.returncode != 0:
                    logger.info(f"Binary {binary} not found. Attempting to download...")
                    if not self.download_binary(binary):
                        raise FileNotFoundError(f"Failed to download and install {binary}")
                    location = subprocess.run(['which', binary], capture_output=True, text=True)
                
                version = subprocess.run(info['version_cmd'], capture_output=True, text=True)
                if version.returncode != 0:
                    raise RuntimeError(f"Failed to get version: {version.stderr}")
                
                self.report.add_success(f"Found {binary} at: {location.stdout.strip()}")
                
            except Exception as e:
                success = False
                self.report.add_error(
                    f"Failed to verify {binary}:\n" +
                    f"  Error: {str(e)}\n" +
                    f"  Install guide: {info['install_guide']}\n" +
                    f"  Verify with: which {binary}"
                )
        
        return success

    def verify_cluster_access(self) -> bool:
        """Verify that we have access to the cluster."""
        self.report.add_section("Cluster Access")
        try:
            result = subprocess.run(['kubectl', 'cluster-info'], capture_output=True, text=True)
            if result.returncode != 0:
                self.report.add_error(
                    "Cannot access Kubernetes cluster:\n" +
                    f"  Error: {result.stderr}\n" +
                    "  Check:\n" +
                    "   - kubectl config view\n" +
                    "   - kubectl cluster-info\n" +
                    "   - kubectl auth can-i get nodes"
                )
                return False
            
            self.report.add_success("Successfully connected to Kubernetes cluster")
            return True
            
        except Exception as e:
            self.report.add_error(
                f"Failed to verify cluster access:\n" +
                f"  Error: {str(e)}\n" +
                "  Check:\n" +
                "   - Cluster is running\n" +
                "   - Network connectivity\n" +
                "   - Kubeconfig is properly set"
            )
            return False

    def deploy_kubewatch_if_needed(self) -> bool:
        """Deploy kubewatch if not already deployed."""
        self.report.add_section("Kubewatch Deployment")
        try:
            # Check if kubewatch is already deployed
            result = subprocess.run(
                ["kubectl", "get", "deployment", "kubewatch", "-n", "default"],
                capture_output=True
            )
            
            if result.returncode == 0:
                self.report.add_success("Kubewatch is already deployed")
                return True

            self.report.add_warning("Kubewatch not found, initiating deployment...")
            if self.kubewatch_deployer.deploy():
                self.report.add_success("Kubewatch deployed successfully")
                return True
            else:
                self.report.add_error("Failed to deploy kubewatch")
                return False

        except Exception as e:
            self.report.add_error(f"Error checking/deploying kubewatch: {str(e)}")
            return False

    def run_verification(self) -> bool:
        """Run all verification checks."""
        self.report.add_section("🔍 KUBERNETES TOOLS VERIFICATION", "=")
        
        checks = [
            (self.verify_binary_installation, "Binary Installation"),
            (self.verify_cluster_access, "Cluster Access"),
            (self.deploy_kubewatch_if_needed, "Kubewatch Deployment"),
        ]
        
        success = True
        for check, name in checks:
            try:
                logger.info(f"🔄 Running verification: {name}")
                if not check():
                    success = False
            except Exception as e:
                success = False
                self.report.add_error(
                    f"Unexpected error in {name}:\n" +
                    f"  Error: {str(e)}"
                )

        if success:
            self.report.add_section("✅ All verifications passed successfully!", "-")
        else:
            self.report.add_section("❌ Some verifications failed. See details above.", "-")

        return success

# Run verifications during import
if __name__ != "__main__":
    verifier = RuntimeVerifier()
    if not verifier.run_verification():
        raise KubernetesVerificationError(
            "One or more verifications failed. Please check the report below for details.",
            verifier.report.get_report()
        )

def run_script(script_content: str, env_vars: dict = None) -> str:
    # Create a temporary script file
    script_path = '/tmp/kubiya_k8s_script.sh'
    with open(script_path, 'w') as f:
        f.write(script_content)
    os.chmod(script_path, 0o700)  # Make the script executable

    # Prepare the environment
    script_env = os.environ.copy()
    if env_vars:
        script_env.update(env_vars)

    # Run the script
    try:
        result = subprocess.run(
            ['/bin/bash', script_path],
            env=script_env,
            check=True,
            capture_output=True,
            text=True
        )
        return result.stdout
    finally:
        # Clean up the temporary script file
        os.remove(script_path)