import subprocess
import shlex
import os
import logging
import json
import time
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

class RuntimeVerifier:
    @staticmethod
    def verify_binary_installation():
        """Verify that required binaries are installed and accessible."""
        binaries = ['kubectl', 'helm']
        for binary in binaries:
            result = subprocess.run(['which', binary], capture_output=True, text=True)
            if result.returncode != 0:
                logger.error(f"❌ {binary} is not installed or not in PATH")
                return False
            logger.info(f"✅ {binary} found at: {result.stdout.strip()}")
        return True

    @staticmethod
    def verify_cluster_access():
        """Verify that we have access to the cluster."""
        try:
            result = subprocess.run(['kubectl', 'cluster-info'], capture_output=True, text=True)
            if result.returncode != 0:
                logger.error(f"❌ Cannot access cluster: {result.stderr}")
                return False
            logger.info("✅ Cluster access verified")
            return True
        except Exception as e:
            logger.error(f"❌ Error verifying cluster access: {str(e)}")
            return False

    @staticmethod
    def verify_permissions():
        """Verify that we have the required permissions."""
        required_permissions = [
            "create clusterrolebinding",
            "create configmap",
            "create deployment",
            "list pods",
            "get pods"
        ]
        
        for permission in required_permissions:
            result = subprocess.run(
                ['kubectl', 'auth', 'can-i'] + permission.split(),
                capture_output=True,
                text=True
            )
            if result.returncode != 0 or 'yes' not in result.stdout.lower():
                logger.error(f"❌ Missing required permission: {permission}")
                return False
        logger.info("✅ All required permissions verified")
        return True

    @staticmethod
    def verify_config_files():
        """Verify that all required config files exist and are valid."""
        required_files = [
            ('config/kubewatch.yaml', 'Kubewatch configuration'),
            ('config/plugins.yaml', 'Plugins configuration')
        ]
        
        base_path = Path(__file__).parent.parent
        for file_path, description in required_files:
            full_path = base_path / file_path
            if not full_path.exists():
                logger.error(f"❌ Missing {description} file: {full_path}")
                return False
            try:
                # Just verify file can be read and is not empty
                with open(full_path) as f:
                    content = f.read().strip()
                    if not content:
                        logger.error(f"❌ Empty {description} file: {full_path}")
                        return False
                logger.info(f"✅ {description} file verified: {full_path}")
            except Exception as e:
                logger.error(f"❌ Invalid {description} file: {str(e)}")
                return False
        return True

    @staticmethod
    def verify_kubewatch_config():
        """Verify kubewatch config can be applied to cluster."""
        try:
            # Try to apply the config directly using kubectl
            config_path = Path(__file__).parent.parent / 'config' / 'kubewatch.yaml'
            result = subprocess.run(
                ['kubectl', 'apply', '--dry-run=client', '-f', str(config_path)],
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                logger.error(f"❌ Invalid kubewatch config: {result.stderr}")
                return False
            logger.info("✅ Kubewatch config validation successful")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to validate kubewatch config: {str(e)}")
            return False

    @staticmethod
    def run_verification():
        """Run all verification checks."""
        checks = [
            RuntimeVerifier.verify_binary_installation,
            RuntimeVerifier.verify_cluster_access,
            RuntimeVerifier.verify_permissions,
            RuntimeVerifier.verify_config_files,
            RuntimeVerifier.verify_kubewatch_config
        ]
        
        results = []
        for check in checks:
            try:
                result = check()
                results.append(result)
                if not result:
                    logger.error(f"❌ Verification failed: {check.__name__}")
            except Exception as e:
                logger.error(f"❌ Error during {check.__name__}: {str(e)}")
                results.append(False)
        
        return all(results)

# Run verifications during import
if __name__ != "__main__":
    logger.info("🔍 Running runtime verifications...")
    if not RuntimeVerifier.run_verification():
        logger.error("❌ Runtime verification failed")
        raise RuntimeError("Failed to verify runtime requirements")
    logger.info("✅ Runtime verification completed successfully")

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