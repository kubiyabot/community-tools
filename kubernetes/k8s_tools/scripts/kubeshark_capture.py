import json
import os
import sys
import time
import subprocess
import argparse
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
import yaml
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

class ProgressReporter:
    def __init__(self, slack_token: Optional[str] = None, channel_id: Optional[str] = None):
        """Initialize progress reporter with optional Slack integration."""
        self.slack_client = WebClient(token=slack_token) if slack_token else None
        self.channel_id = channel_id
        self.message_ts = None
        self.start_time = time.time()

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
    def __init__(self, output_dir: Path):
        """Initialize Kubeshark capture with progress reporting."""
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize progress reporter
        slack_token = os.getenv('SLACK_API_TOKEN')
        slack_channel = os.getenv('SLACK_CHANNEL_ID')
        self.progress = ProgressReporter(slack_token, slack_channel)
        
        # Capture configuration
        self.kubeshark_host = os.getenv('KUBESHARK_HOST', '127.0.0.1')
        self.kubeshark_port = os.getenv('KUBESHARK_PORT', '8899')

    def capture_traffic(self, filter_expr: str, duration: int, namespace: Optional[str] = None):
        """Capture traffic with real-time progress updates."""
        self.progress.console_progress("Starting traffic capture", "🚀")
        self.progress.update_slack_progress(
            "Starting Capture",
            1, 4,
            {"current_operation": "Initializing capture"}
        )

        # Verify environment
        self.progress.console_progress("Verifying Kubeshark availability", "🔍", 1)
        self._verify_kubeshark()

        # Initialize capture
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = self.output_dir / f"traffic_{timestamp}.json"
        
        # Start capture with progress tracking
        captured_entries = 0
        start_time = time.time()
        
        try:
            with self._start_capture(filter_expr, duration) as process:
                self.progress.console_progress("Capturing traffic", "📥", 1)
                
                while process.poll() is None:
                    line = process.stdout.readline()
                    if line:
                        captured_entries += 1
                        if captured_entries % 100 == 0:  # Update every 100 entries
                            elapsed = time.time() - start_time
                            rate = captured_entries / elapsed if elapsed > 0 else 0
                            
                            self.progress.update_slack_progress(
                                "Capturing Traffic",
                                2, 4,
                                {
                                    "current_operation": "Processing network traffic",
                                    "metrics": {
                                        "Captured Entries": captured_entries,
                                        "Capture Rate": f"{rate:.1f} entries/sec",
                                        "Elapsed Time": f"{int(elapsed)}s"
                                    }
                                }
                            )

        except Exception as e:
            self.progress.console_progress(f"Error during capture: {str(e)}", "❌", 1)
            self.progress.update_slack_progress(
                "Capture Failed",
                2, 4,
                {"current_operation": "Error occurred"},
                str(e)
            )
            raise

        self.progress.console_progress("Traffic capture completed", "✅", 1)
        return output_file

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

if __name__ == "__main__":
    main() 