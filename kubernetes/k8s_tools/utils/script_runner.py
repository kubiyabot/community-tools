import subprocess
import shlex
import os
import logging
import json
from pathlib import Path
from typing import Optional
from collections import defaultdict
from io import StringIO
import sys

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

    def verify_binary_installation(self, binaries: dict) -> bool:
        """Verify that required binaries are installed."""
        self.report.add_section("Binary Dependencies")
        success = True

        for binary, info in binaries.items():
            try:
                location = subprocess.run(['which', binary], capture_output=True, text=True)
                if location.returncode != 0:
                    self.report.add_error(f"Binary {binary} not found")
                    success = False
                    continue
                
                version = subprocess.run(info['version_cmd'], capture_output=True, text=True)
                if version.returncode != 0:
                    self.report.add_error(f"Failed to get {binary} version: {version.stderr}")
                    success = False
                    continue
                
                self.report.add_success(f"Found {binary} at: {location.stdout.strip()}")
                
            except Exception as e:
                success = False
                self.report.add_error(f"Error verifying {binary}: {str(e)}")
        
        return success

    def verify_cluster_access(self) -> bool:
        """Verify that we have access to the cluster."""
        self.report.add_section("Cluster Access")
        try:
            result = subprocess.run(['kubectl', 'cluster-info'], capture_output=True, text=True)
            if result.returncode != 0:
                self.report.add_error(f"Cannot access cluster: {result.stderr}")
                return False
            
            self.report.add_success("Successfully connected to cluster")
            return True
            
        except Exception as e:
            self.report.add_error(f"Failed to verify cluster access: {str(e)}")
            return False

    def verify_deployment(self, name: str, namespace: str) -> bool:
        """Verify that a deployment exists and is running."""
        self.report.add_section(f"Deployment: {name}")
        try:
            result = subprocess.run(
                ['kubectl', 'get', 'deployment', name, '-n', namespace],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                self.report.add_success(f"Deployment {name} exists in namespace {namespace}")
                return True
            else:
                self.report.add_error(f"Deployment {name} not found in namespace {namespace}")
                return False

        except Exception as e:
            self.report.add_error(f"Error checking deployment {name}: {str(e)}")
            return False

def run_script(script_content: str, env_vars: dict = None) -> str:
    """Run a shell script with environment variables."""
    script_path = '/tmp/kubiya_k8s_script.sh'
    with open(script_path, 'w') as f:
        f.write(script_content)
    os.chmod(script_path, 0o700)

    try:
        result = subprocess.run(
            ['/bin/bash', script_path],
            env={**os.environ, **(env_vars or {})},
            check=True,
            capture_output=True,
            text=True
        )
        return result.stdout
    finally:
        os.remove(script_path)