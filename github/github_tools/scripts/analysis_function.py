import os
import sys
import requests  # Import requests for making API calls
from mem0 import MemoryClient  # Uncomment this line to use MemoryClient
from openai import OpenAI  # Updated import statement
from litellm import completion  # Updated import statement

# Define the AI analysis prompt as a constant
ANALYSIS_PROMPT = """
You are an expert developer and code reviewer. Analyze the following pull request (PR) based on the provided content:
1. Summarize the purpose and key changes in the PR.
2. Identify any potential issues or improvements in the code.
3. Highlight any code smells or potential refactoring opportunities.
4. Provide recommendations for testing or additional documentation.
5. Ensure to use concise, clear, and actionable feedback.

Please provide the analysis in the following format:
conclusion: ...
score: ...

PR Content:
"""

def analyze_pr(pr_content, user_email, repo):
    """
    Analyzes a pull request (PR) using OpenAI and Mem0.

    Args:
        pr_content (str): The content of the PR (text).
        mem0_api_key (str): API key for Mem0.
        openai_api_key (str): API key for OpenAI.
        user_id (str): A unique identifier for the user (default is 'default_user').

    Returns:
        None
    """
    # Initialize Mem0 client
    memory_client = MemoryClient(api_key="m0-7TIHSrRBHv1CNO6bvsjQUEEsc5kguHhesNFMjdwN")

    # Initialize Litellm client
    llm_key = "sk-2YfBaZ9HM-xfViulI4zJgw"  # os.environ["VISION_LLM_KEY"]
    llm_base_url = "https://llm-proxy.kubiya.ai"  # os.environ["VISION_LLM_BASE_URL"]
    # openai call
    try:
        response = completion(  # Updated to use litellm
            model="openai/gpt-4o",
            api_key=llm_key,
            base_url=llm_base_url,
            messages=[
                {
                    "role": "system",
                    "content": "You are a highly skilled code reviewer.",  # SYSTEM_PROMPT
                },
                {
                    "role": "user",
                    "content": f"{ANALYSIS_PROMPT}{pr_content} \n\n repo: {repo}",
                }
            ],
        )
    except Exception as e:
        print(f"Error during LLM call: {str(e)}")

    # Construct message for memory with AI result
    ai_result_message = [
        {"role": "system", "content": response['choices'][0]['message']['content']}
    ]

    # Save AI result to Mem0
    memory_client.add(ai_result_message, user_id=user_email)

    # Print the analysis output
    print(response['choices'][0]['message']['content'])

def main():
    """Main function to handle comment generation."""
    try:
        # Get variables from environment
        required_vars = [
            'ANALYSIS', 'USER_EMAIL', 'REPO'# Added required API keys
        ]
        
        variables = {}
        for var in required_vars:
            if var not in os.environ:
                print(f"Missing required environment variable: {var}")
                raise KeyError(f"Missing required environment variable: {var}")
            variables[var.lower()] = os.environ[var]

        # Example usage of analyze_pr function
        analyze_pr(variables['analysis'], variables['user_email'], variables['repo'])  # Uncommented and adjusted

        print("Comment generation completed successfully")
        
    except KeyError as e:
        print(f"Missing environment variable: {str(e)}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()