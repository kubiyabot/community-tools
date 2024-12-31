import os
import logging
import argparse
import requests
import openai
from typing import Dict, Optional
from utils.slack_messages import SlackMessage
from utils.log_analyzer import analyze_logs_with_llm

INSTENV_API_BASE_DEFAULT_ENDPOINT = "https://dev.instenv-ui.internal.atlassian.com/api/v1"
INSTENV_LOG_TAIL_LINES = 200

class InstEnvAPI:
    __env_cached_response: Optional[Dict] = None

    def __init__(self, env_id, api_key, api_base_endpoint=None):
        self.env_id = env_id
        self.api_key = api_key
        self.api_base_endpoint = api_base_endpoint or INSTENV_API_BASE_DEFAULT_ENDPOINT
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def get_env_info(self) -> Dict:
        if not self.__env_cached_response:
            try:
                url = f"{self.api_base_endpoint}/environments/{self.env_id}"
                logging.debug(f"Requesting URL: {url}")
                response = requests.get(url, headers=self.headers)
                response.raise_for_status()
                self.__env_cached_response = response.json()
                logging.debug(f"Got env info: {self.__env_cached_response}")
            except requests.exceptions.HTTPError as http_err:
                logging.error(f"HTTP error occurred: {http_err}")
                raise
            except Exception as err:
                logging.error(f"Other error occurred: {err}")
                raise
        return self.__env_cached_response

    def get_latest_failed_run(self) -> Optional[Dict]:
        env_info = self.get_env_info()
        sorted_runs = sorted(env_info.get("runs", []), key=lambda x: x.get("failed_at", ""))
        if sorted_runs:
            return sorted_runs[0]
        return None

    def analyze_failure(self, failed_run: Dict) -> str:
        """Analyze failure using OpenAI."""
        openai.api_key = os.environ["OPENAI_API_KEY"]
        if os.environ.get("OPENAI_API_BASE"):
            openai.api_base = os.environ["OPENAI_API_BASE"]

        prompt = f"""
        Analyze this environment failure and provide suggestions to fix the issues:
        
        Environment ID: {self.env_id}
        Failure Details: {failed_run}
        
        Please provide:
        1. Root cause analysis
        2. Potential solutions
        3. Prevention recommendations
        """

        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}]
        )

        return response.choices[0].message.content

    def get_latest_run_logs(self, log_tail_lines: int = INSTENV_LOG_TAIL_LINES) -> Optional[str]:
        """Get logs from the latest failed run."""
        latest_run = self.get_latest_failed_run()
        if latest_run and latest_run.get("logs_url"):
            try:
                response = requests.get(latest_run.get("logs_url"), headers=self.headers)
                response.raise_for_status()
                fixed_log = response.text.strip().strip("\"").replace('\\n', os.linesep)
                logging.debug("Retrieved latest run logs")
                return self.__get_last_n_lines(
                    log=fixed_log,
                    n=log_tail_lines
                ) if log_tail_lines > 0 else fixed_log
            except Exception as err:
                logging.error(f"Error fetching logs: {err}")
                raise
        return None

    @staticmethod
    def __get_last_n_lines(log: str, n: int) -> str:
        return os.linesep.join(log.split(os.linesep)[-n:])

def main():
    parser = argparse.ArgumentParser(description='Analyze environment failure logs.')
    parser.add_argument('--env_id', type=str, help='Environment ID', required=True)
    args = parser.parse_args()

    try:
        api_key = os.environ.get("INSTENV_API_KEY")
        if not api_key:
            raise ValueError("INSTENV_API_KEY environment variable is required")

        api = InstEnvAPI(args.env_id, api_key)
        logs = api.get_latest_run_logs()

        if logs:
            logging.info("Retrieved failure logs, analyzing...")
            try:
                analysis_results = analyze_logs_with_llm(logs)
                blocks = []
                for item in analysis_results:
                    block = {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": (
                                f"*Reason of the failure:*\n{item.reason}\n"
                                f"*How to fix:*\n{item.how_to_fix}\n"
                                f"*Changes in JSON payload:*\n{item.suggested_payload_changes}\n"
                            )
                        }
                    }
                    blocks.append(block)
                
                slack_message = SlackMessage(channel=os.getenv('SLACK_CHANNEL_ID'))
                slack_message.send_initial_message(blocks)
                
            except Exception as e:
                logging.error(f"Failed to analyze logs: {e}")
                raise
        else:
            print("No logs available for the latest failed run.")

    except Exception as e:
        logging.error(f"Error in main function: {e}")
        raise

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG if os.environ.get("DEBUG", "").lower() in ["1", "true"] else logging.INFO
    )
    main() 