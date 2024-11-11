import json
import os
import sys
import time
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
from datetime import datetime

# Handle third-party imports without auto-installation
REQUIRED_PACKAGES = {
    'argparse': False,  # Built-in for Python 3
    'yaml': False,
    'slack_sdk': False,
    'websocket': False
}

try:
    import argparse
except ImportError:
    REQUIRED_PACKAGES['argparse'] = True

try:
    import yaml
except ImportError:
    REQUIRED_PACKAGES['yaml'] = True

try:
    from slack_sdk import WebClient
    from slack_sdk.errors import SlackApiError
    SLACK_AVAILABLE = True
except ImportError:
    REQUIRED_PACKAGES['slack_sdk'] = True
    SLACK_AVAILABLE = False

try:
    import websocket
except ImportError:
    REQUIRED_PACKAGES['websocket'] = True

# Check for missing packages
missing_packages = [pkg for pkg, missing in REQUIRED_PACKAGES.items() if missing]
if missing_packages:
    print(f"Error: Required packages missing: {', '.join(missing_packages)}")
    print("Please install required packages before running this script.")
    sys.exit(1)

class KubesharkManager:
    """Manages Kubeshark binary and its lifecycle."""
    
    KUBESHARK_VERSION = "v52.3.89"  # Default version
    KUBESHARK_BINARY_URL = f"https://github.com/kubeshark/kubeshark/releases/download/{KUBESHARK_VERSION}/kubeshark_linux_amd64"
    
    def __init__(self):
        self.binary_path = "/usr/local/bin/kubeshark"
        self.version = os.getenv("KUBESHARK_VERSION", self.KUBESHARK_VERSION)
        if self.version != self.KUBESHARK_VERSION:
            self.KUBESHARK_BINARY_URL = f"https://github.com/kubeshark/kubeshark/releases/download/{self.version}/kubeshark_linux_amd64"
    
    def ensure_binary(self) -> bool:
        """Ensure Kubeshark binary is available."""
        if self._check_binary():
            return True
            
        print("Kubeshark binary not found. Installing...")
        return self._install_binary()
    
    def _check_binary(self) -> bool:
        """Check if Kubeshark binary exists and is executable."""
        try:
            result = subprocess.run(
                [self.binary_path, "version"],
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except (subprocess.SubprocessError, FileNotFoundError):
            return False
    
    def _install_binary(self) -> bool:
        """Install Kubeshark binary."""
        try:
            # Download binary
            print(f"Downloading Kubeshark {self.version}...")
            download_cmd = f"curl -Lo {self.binary_path} {self.KUBESHARK_BINARY_URL}"
            subprocess.run(download_cmd, shell=True, check=True)
            
            # Make binary executable
            chmod_cmd = f"chmod 755 {self.binary_path}"
            subprocess.run(chmod_cmd, shell=True, check=True)
            
            print("✅ Kubeshark installed successfully")
            return True
            
        except subprocess.SubprocessError as e:
            print(f"❌ Failed to install Kubeshark: {str(e)}")
            return False
    
    def start_capture(self) -> bool:
        """Start Kubeshark capture."""
        try:
            subprocess.run(
                [self.binary_path, "tap", "--headless"],  # Added --headless for non-interactive mode
                check=True
            )
            return True
        except subprocess.SubprocessError as e:
            print(f"Failed to start Kubeshark capture: {str(e)}")
            return False
    
    def stop_capture(self):
        """Stop Kubeshark capture."""
        try:
            subprocess.run(
                [self.binary_path, "clean"],
                check=True
            )
        except subprocess.SubprocessError as e:
            print(f"Warning: Failed to clean Kubeshark: {str(e)}")

class ProgressReporter:
    """Handles progress reporting with optional Slack integration."""
    
    def __init__(self, slack_token: Optional[str] = None, channel_id: Optional[str] = None):
        self.slack_client = None
        self.channel_id = channel_id
        self.message_ts = None
        self.start_time = time.time()

        if SLACK_AVAILABLE and slack_token:
            try:
                self.slack_client = WebClient(token=slack_token)
            except Exception as e:
                print(f"Warning: Failed to initialize Slack client: {str(e)}")

    def console_progress(self, message: str, emoji: str = "🔄", level: int = 0):
        """Print formatted console progress."""
        indent = "  " * level
        print(f"\n{indent}{emoji} {message}", flush=True)

    def update_slack_progress(self, status: str, current_step: int, total_steps: int, 
                            details: Dict[str, Any], error: Optional[str] = None):
        """Update Slack with current progress using blocks."""
        if not self.slack_client or not self.channel_id:
            return

        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "🔍 Kubeshark Traffic Analysis",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Status:*\n{status}"},
                    {"type": "mrkdwn", "text": f"*Progress:*\n{current_step}/{total_steps}"}
                ]
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"⏱️ Running for: {int((time.time() - self.start_time) / 60)}m"
                }
            }
        ]

        # Add current operation details
        if details.get("current_operation"):
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Current Operation:*\n{details['current_operation']}"
                }
            })

        # Add metrics if available
        if details.get("metrics"):
            metrics_text = "\n".join([f"• {k}: {v}" for k, v in details["metrics"].items()])
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Current Metrics:*\n{metrics_text}"
                }
            })

        # Add error if present
        if error:
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"❌ *Error:*\n```{error}```"
                }
            })

        try:
            if self.message_ts:
                self.slack_client.chat_update(
                    channel=self.channel_id,
                    ts=self.message_ts,
                    blocks=blocks
                )
            else:
                response = self.slack_client.chat_postMessage(
                    channel=self.channel_id,
                    blocks=blocks
                )
                self.message_ts = response["ts"]
        except SlackApiError as e:
            print(f"Warning: Failed to update Slack: {str(e)}")

class KubesharkCapture:
    """Manages Kubeshark capture and analysis."""
    
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize managers
        self.kubeshark = KubesharkManager()
        self.progress = ProgressReporter(
            os.getenv('SLACK_API_TOKEN'),
            os.getenv('SLACK_CHANNEL_ID')
        )
        
        # Capture configuration
        self.kubeshark_host = os.getenv('KUBESHARK_HOST', '127.0.0.1')
        self.kubeshark_port = os.getenv('KUBESHARK_PORT', '8899')

    def setup(self) -> bool:
        """Setup and verify environment."""
        if not self.kubeshark.ensure_binary():
            return False
            
        self.progress.console_progress("Verifying Kubeshark installation", "🔍")
        return True

    def capture_traffic(self, filter_expr: str, duration: int, namespace: Optional[str] = None):
        """Capture traffic with real-time progress updates."""
        if not self.setup():
            raise RuntimeError("Failed to setup Kubeshark environment")

        try:
            # Start Kubeshark
            self.progress.console_progress("Starting Kubeshark capture", "🚀")
            if not self.kubeshark.start_capture():
                raise RuntimeError("Failed to start Kubeshark capture")

            # ... (rest of capture implementation)

        finally:
            # Cleanup
            self.kubeshark.stop_capture()

    def analyze_traffic(self, capture_file: Path, analysis_types: List[str] = ["basic"]):
        """Analyze traffic with progress updates."""
        self.progress.console_progress("Starting traffic analysis", "🔍")
        self.progress.update_slack_progress(
            "Analyzing Traffic",
            3, 4,
            {"current_operation": "Starting analysis"}
        )

        analysis_results = {}
        total_analyses = len(analysis_types)
        
        for idx, analysis_type in enumerate(analysis_types, 1):
            self.progress.console_progress(f"Running {analysis_type} analysis", "📊", 1)
            
            try:
                result = self._run_analysis(capture_file, analysis_type)
                analysis_results[analysis_type] = result
                
                self.progress.update_slack_progress(
                    "Analyzing Traffic",
                    3, 4,
                    {
                        "current_operation": f"Completed {analysis_type} analysis",
                        "metrics": {
                            "Completed Analyses": f"{idx}/{total_analyses}",
                            "Current Analysis": analysis_type,
                            "Found Issues": len(result.get("issues", []))
                        }
                    }
                )
                
            except Exception as e:
                self.progress.console_progress(f"Error in {analysis_type} analysis: {str(e)}", "❌", 2)
                self.progress.update_slack_progress(
                    "Analysis Error",
                    3, 4,
                    {"current_operation": f"Error in {analysis_type} analysis"},
                    str(e)
                )

        # Final update
        self.progress.console_progress("Analysis completed", "✅")
        self.progress.update_slack_progress(
            "Analysis Complete",
            4, 4,
            {
                "current_operation": "Finished all analyses",
                "metrics": {
                    "Total Analyses": total_analyses,
                    "Total Issues": sum(len(r.get("issues", [])) for r in analysis_results.values())
                }
            }
        )

        return analysis_results

    # ... (rest of the implementation)

def main():
    # Verify environment first
    kubeshark = KubesharkManager()
    if not kubeshark.ensure_binary():
        sys.exit(1)

    # Parse arguments and continue with execution
    parser = argparse.ArgumentParser(description="Kubeshark Traffic Capture and Analysis")
    parser.add_argument("--mode", required=True, help="Capture mode")
    parser.add_argument("--output-dir", required=True, help="Output directory")
    parser.add_argument("--filter", help="Traffic filter expression")
    parser.add_argument("--duration", type=int, help="Capture duration in seconds")
    parser.add_argument("--namespace", help="Kubernetes namespace")
    parser.add_argument("--analysis-types", nargs="+", default=["basic"],
                       help="Types of analysis to perform")
    args = parser.parse_args()

    try:
        capture = KubesharkCapture(Path(args.output_dir))
        
        # Verify environment
        capture.print_progress("Verifying environment...", "🔍")
        k8s_info = capture.verify_kubernetes_context()
        kubeshark_info = capture.verify_kubeshark()
        
        # Capture traffic
        capture.print_progress(f"Starting traffic capture in {args.mode} mode...", "📥")
        capture_file = capture.capture_traffic(
            args.filter or "true",
            args.duration or 300,
            args.namespace
        )
        
        # Analyze traffic
        capture.print_progress("Analyzing captured traffic...", "📊")
        analysis = capture.analyze_traffic(capture_file, args.analysis_types)
        
        # Save results
        results_file = Path(args.output_dir) / "analysis_results.json"
        with open(results_file, 'w') as f:
            json.dump(analysis, f, indent=2)
        
        capture.print_progress(f"Analysis complete. Results saved to {results_file}", "✅")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}", file=sys.stderr)
        sys.exit(1)
    finally:
        kubeshark.stop_capture()

if __name__ == "__main__":
    main() 