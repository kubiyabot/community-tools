import logging
import json
from typing import List
from litellm import completion
from pydantic import BaseModel, ValidationError
from time import sleep

class DetailedLLMResponse(BaseModel):
    reason: str
    how_to_fix: str
    suggested_payload_changes: str

def analyze_logs_with_llm(logs: str, max_retries: int = 10, delay: int = 2) -> List[DetailedLLMResponse]:
    sys_prompt = (
        f"You are a ChatGPT-based system integrated into a DevOps environment. Your role is to analyze issues related to environment creation failures from an Ansible logs database and provide troubleshooting advice. The answers should be comprehensible to non-technical users, focusing on issues specific to Atlassian Instenv, explicitly excluding Kubernetes-related scenarios. "
        f"\n\n{logs}\n\n"
        "When the knowledge base does not contain the answer, you will fetch relevant details from the Ansible logs via API. Each response should pinpoint a single primary issue cause and offer a concise, actionable solution. "
        "Return a response in the following structure:\n"
        "[\n"
        "   {\n"
        "       \"reason\": \"{reason}\",\n"
        "       \"how_to_fix\": \"{how_to_fix}\",\n"
        "       \"suggested_payload_changes\": \"{suggested_payload_changes}\"\n"
        "   }\n"
        "]"
    )
    messages = [{"content": sys_prompt, "role": "system"}]

    for attempt in range(max_retries):
        try:
            response = completion(
                model="gpt-4o",
                messages=messages,
                format="json"
            )
            llm_response = response['choices'][0]['message']['content']
            try:
                # Ensure the response is correctly formatted JSON
                if llm_response.startswith("```json"):
                    llm_response = llm_response[7:]
                if llm_response.endswith("```"):
                    llm_response = llm_response[:-3]
                parsed_response = json.loads(llm_response)
                return [DetailedLLMResponse(**item) for item in parsed_response]
            except (json.JSONDecodeError, ValidationError) as e:
                logging.error(f"Error parsing response on attempt {attempt + 1}/{max_retries}: {e}")
                if attempt < max_retries - 1:
                    sleep(delay)
                else:
                    raise
        except Exception as e:
            logging.error(f"Error on attempt {attempt + 1}/{max_retries}: {e}")
            if attempt < max_retries - 1:
                sleep(delay)
            else:
                raise 