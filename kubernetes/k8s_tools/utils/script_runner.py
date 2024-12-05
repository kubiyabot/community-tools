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

class RuntimeVerifier:
    def __init__(self):
        self.report = VerificationReport()
        self.errors = defaultdict(list)
        self.warnings = defaultdict(list)

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
                
                response = requests.get(download_url)
                with open(binary_path, 'wb') as f:
                    f.write(response.content)
                
                # Make executable
                os.chmod(binary_path, 0o755)
                return True
                
            elif binary == 'helm':
                # Download Helm install script
                script_url = "https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3"
                script_path = "/tmp/get_helm.sh"
                
                response = requests.get(script_url)
                with open(script_path, 'wb') as f:
                    f.write(response.content)
                
                # Make executable and run
                os.chmod(script_path, 0o755)
                subprocess.run([script_path], check=True)
                os.remove(script_path)
                return True
                
        except Exception as e:
            logger.error(f"Failed to download {binary}: {str(e)}")
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

    def run_verification(self) -> bool:
        """Run all verification checks."""
        self.report.add_section("🔍 KUBERNETES TOOLS VERIFICATION", "=")
        
        checks = [
            (self.verify_binary_installation, "Binary Installation"),
            (self.verify_cluster_access, "Cluster Access"),
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