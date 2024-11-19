from time import sleep
from typing import Any, Dict
from pydantic import BaseModel, ValidationError
from litellm import completion
import json

class CodeUnrecoverableLLMResponse(BaseModel):
    unrecoverable_error: bool
    reasoning: str

def is_error_unrecoverable(error: str, max_retries: int = 10, delay: int = 2) -> CodeUnrecoverableLLMResponse:
    sys_prompt = f"Carefully read the following output from Terraform and classify the error as recoverable or unrecoverable. Unrecoverable errors are those that require manual intervention to resolve (eg. resource name already exists). If the error is unrecoverable, provide a brief reasoning for why it is unrecoverable.\n\n{error}\n\nReturn a VALID JSON response with the following structure:\n{{\n    \"unrecoverable_error\": bool,\n    \"reasoning\": \"string\"\n}}"
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
                # Parse the response to ensure it is valid JSON and matches the expected format
                parsed_response: Dict[str, Any] = json.loads(llm_response)
                return CodeUnrecoverableLLMResponse(**parsed_response)
            except json.JSONDecodeError as e:
                print(f"Attempt {attempt + 1}/{max_retries} failed with error: {e}")
                if attempt < max_retries - 1:
                    sleep(delay)
                else:
                    raise e
            except ValidationError as e:
                print(f"Attempt {attempt + 1}/{max_retries} failed with error: {e}")
                if attempt < max_retries - 1:
                    sleep(delay)
                else:
                    raise e
        except Exception as e:
            print(f"Attempt {attempt + 1}/{max_retries} failed with error: {e}")
            if attempt < max_retries - 1:
                sleep(delay)
            else:
                raise e
