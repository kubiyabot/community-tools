import subprocess
import shlex
import os
import logging
import json
import time
import sys
from pathlib import Path
from typing import List, Dict, Any, Tuple
from collections import defaultdict

# Configure detailed logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class VerificationError(Exception):
    """Custom exception for verification failures with detailed information."""
    def __init__(self, message: str, component: str, details: Any = None, recommendations: List[str] = None):
        self.message = message
        self.component = component
        self.details = details
        self.recommendations = recommendations or []
        super().__init__(self.format_message())

    def format_message(self) -> str:
        msg = [
            f"\n{'='*80}",
            f"❌ Verification Failed: {self.component}",
            f"{'='*80}",
            f"\n🔍 Error: {self.message}",
        ]
        
        if self.details:
            msg.extend([
                "\n📋 Details:",
                f"{json.dumps(self.details, indent=2) if isinstance(self.details, (dict, list)) else str(self.details)}"
            ])
        
        if self.recommendations:
            msg.extend([
                "\n💡 Recommendations:",
                *[f"  • {rec}" for rec in self.recommendations]
            ])
        
        msg.extend([
            "\n⚠️  Action Required: Please fix the above issues and try again.",
            f"{'='*80}\n"
        ])
        
        return "\n".join(msg)

class RuntimeVerifier:
    def __init__(self):
        self.errors = defaultdict(list)
        self.warnings = defaultdict(list)
        self.missing_dependencies = set()

    def add_error(self, component: str, error: VerificationError):
        """Add an error to the collection."""
        self.errors[component].append(error)

    def add_warning(self, component: str, message: str, details: Any = None):
        """Add a warning to the collection."""
        self.warnings[component].append({"message": message, "details": details})

    def check_python_dependencies(self) -> bool:
        """Check required Python dependencies."""
        required_packages = ['kubernetes', 'yaml']
        for package in required_packages:
            try:
                __import__(package)
                logger.info(f"✅ Found required package: {package}")
            except ImportError:
                self.missing_dependencies.add(package)
                self.add_error(
                    "Dependencies",
                    VerificationError(
                        f"Missing required Python package: {package}",
                        "Python Dependencies",
                        recommendations=[
                            f"Install the package: pip install {package}",
                            "Add the package to requirements.txt",
                            f"Verify package is available: python -c 'import {package}'"
                        ]
                    )
                )
        return len(self.missing_dependencies) == 0

    def verify_binary_installation(self) -> bool:
        """Verify that required binaries are installed and accessible."""
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
        
        all_found = True
        for binary, info in binaries.items():
            try:
                # Check if binary exists
                location = subprocess.run(['which', binary], capture_output=True, text=True)
                if location.returncode != 0:
                    raise FileNotFoundError(f"Binary not found: {binary}")
                
                # Check version
                version = subprocess.run(info['version_cmd'], capture_output=True, text=True)
                if version.returncode != 0:
                    raise RuntimeError(f"Failed to get version: {version.stderr}")
                
                logger.info(f"✅ Found {binary} at: {location.stdout.strip()}")
                
            except Exception as e:
                all_found = False
                self.add_error(
                    "Binary Installation",
                    VerificationError(
                        f"Failed to verify {binary}",
                        "Binary Dependencies",
                        details=str(e),
                        recommendations=[
                            f"Install {binary} following: {info['install_guide']}",
                            f"Ensure {binary} is in PATH: echo $PATH",
                            f"Verify installation: which {binary}"
                        ]
                    )
                )
        
        return all_found

    def verify_cluster_access(self) -> bool:
        """Verify that we have access to the cluster."""
        try:
            result = subprocess.run(
                ['kubectl', 'cluster-info'], 
                capture_output=True, 
                text=True
            )
            if result.returncode != 0:
                self.add_error(
                    "Cluster Access",
                    VerificationError(
                        "Cannot access Kubernetes cluster",
                        "Cluster Configuration",
                        details=result.stderr,
                        recommendations=[
                            "Check kubeconfig file: kubectl config view",
                            "Verify cluster status: kubectl cluster-info",
                            "Check network connectivity to cluster",
                            "Verify credentials: kubectl auth can-i get nodes"
                        ]
                    )
                )
                return False
            
            logger.info("✅ Cluster access verified")
            return True
            
        except Exception as e:
            self.add_error(
                "Cluster Access",
                VerificationError(
                    "Failed to verify cluster access",
                    "Cluster Configuration",
                    details=str(e),
                    recommendations=[
                        "Ensure kubectl is properly configured",
                        "Check if cluster is running",
                        "Verify network connectivity"
                    ]
                )
            )
            return False

    def print_verification_report(self):
        """Print a detailed verification report."""
        print("\n" + "="*80)
        print("🔍 KUBERNETES TOOLS VERIFICATION REPORT")
        print("="*80 + "\n")

        if self.errors:
            print("❌ ERRORS:")
            for component, error_list in self.errors.items():
                for error in error_list:
                    print(error.format_message())

        if self.warnings:
            print("\n⚠️  WARNINGS:")
            for component, warning_list in self.warnings.items():
                for warning in warning_list:
                    print(f"\n{component}:")
                    print(f"  • {warning['message']}")
                    if warning['details']:
                        print(f"    Details: {warning['details']}")

        if not self.errors and not self.warnings:
            print("✅ All verifications passed successfully!")

        print("\n" + "="*80)

    def run_verification(self) -> bool:
        """Run all verification checks."""
        checks = [
            (self.check_python_dependencies, "Python Dependencies"),
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
                self.add_error(
                    name,
                    VerificationError(
                        "Unexpected error during verification",
                        name,
                        details=str(e)
                    )
                )

        self.print_verification_report()
        return success

# Run verifications during import
if __name__ != "__main__":
    verifier = RuntimeVerifier()
    if not verifier.run_verification():
        raise RuntimeError("Failed to verify runtime requirements. See above report for details.")

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