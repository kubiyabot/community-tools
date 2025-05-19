from typing import List, Optional, Dict, Any
from kubiya_sdk.tools import Tool, Arg, FileSpec
import json

CONFLUENCE_ICON_URL = "https://cdn.worldvectorlogo.com/logos/confluence-1.svg"

DEFAULT_MERMAID = """
```mermaid
classDiagram
    class Tool {
        <<interface>>
        +get_args()
        +get_content()
        +get_image()
    }
    class ConfluenceTool {
        -content: str
        -args: List[Arg]
        -image: str
        +__init__(name, description, content, args, image)
        +get_args()
        +get_content()
        +get_image()
        +get_file_specs()
        +validate_args(args)
        +get_error_message(args)
        +get_environment()
    }
    Tool <|-- ConfluenceTool
```
"""

class ConfluenceTool(Tool):
    """Base class for all Confluence tools."""
    
    name: str
    description: str
    content: str = ""
    args: List[Arg] = []
    image: str = "curlimages/curl:8.1.2"
    icon_url: str = CONFLUENCE_ICON_URL
    type: str = "docker"
    mermaid: str = DEFAULT_MERMAID
    
    def __init__(self, name, description, content, args=None, image="curlimages/curl:8.1.2", 
                 env=None, secrets=None, with_files=None):
        # Add basic validation function to the content
        helper_functions = """
            # Basic validation function for Confluence tools
            validate_confluence_connection() {
                if [ -z "$CONFLUENCE_URL" ]; then
                    echo "Error: CONFLUENCE_URL environment variable is required"
                    exit 1
                fi

                if [ -z "$CONFLUENCE_API_TOKEN" ] || [ -z "$CONFLUENCE_USERNAME" ]; then
                    echo "Error: CONFLUENCE_API_TOKEN and CONFLUENCE_USERNAME environment variables are required"
                    exit 1
                fi
                
                # Print connection details for debugging (without exposing the full token)
                echo "Attempting to connect to: $CONFLUENCE_URL"
                echo "Using username: $CONFLUENCE_USERNAME"
                echo "API Token: ${CONFLUENCE_API_TOKEN:0:3}...${CONFLUENCE_API_TOKEN: -3}"
            }
        """
        
        content = helper_functions + "\n" + content
        
        # Combine default environment variables with any additional ones
        all_env = ["CONFLUENCE_URL", "CONFLUENCE_USERNAME"]
        if env:
            all_env.extend(env)
        
        # Combine default secrets with any additional ones
        all_secrets = ["CONFLUENCE_API_TOKEN"]
        if secrets:
            all_secrets.extend(secrets)
        
        super().__init__(
            name=name,
            description=description,
            content=content,
            args=args or [],
            image=image,
            icon_url=CONFLUENCE_ICON_URL,
            type="docker",
            secrets=all_secrets,
            env=all_env,
            with_files=with_files
        )

    def get_args(self) -> List[Arg]:
        """Return the tool's arguments."""
        return self.args

    def get_content(self) -> str:
        """Return the tool's shell script content."""
        return self.content

    def get_image(self) -> str:
        """Return the Docker image to use."""
        return self.image

    def validate_args(self, args: Dict[str, Any]) -> bool:
        """Validate the provided arguments."""
        required_args = [arg.name for arg in self.args if arg.required]
        return all(arg in args and args[arg] for arg in required_args)

    def get_error_message(self, args: Dict[str, Any]) -> Optional[str]:
        """Return error message if arguments are invalid."""
        missing_args = []
        for arg in self.args:
            if arg.required and (arg.name not in args or not args[arg.name]):
                missing_args.append(arg.name)
        
        if missing_args:
            return f"Missing required arguments: {', '.join(missing_args)}"
        return None 
    
class ContentAnalyzerTool(Tool):
    def __init__(self, name, description, args, mermaid_diagram=None):
        env = ["CONFLUENCE_URL", "CONFLUENCE_USERNAME", "KUBIYA_USER_EMAIL", "LLM_BASE_URL"]
        secrets = ["CONFLUENCE_API_TOKEN", "LLM_API_KEY"]
        
        arg_names_json = json.dumps([arg.name for arg in args])
        
        script_content = f"""
import os
import sys
import json
import logging
import requests
import litellm
from typing import Dict, List, Any, Tuple, Optional

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def validate_confluence_connection() -> Tuple[bool, str]:
    confluence_url = os.environ.get("CONFLUENCE_URL", "")
    username = os.environ.get("CONFLUENCE_USERNAME", "")
    api_token = os.environ.get("CONFLUENCE_API_TOKEN", "")
    
    if not confluence_url or not username or not api_token:
        return False, "Confluence credentials not properly configured"
    
    # Test the connection
    try:
        url = f"{{confluence_url.rstrip('/')}}/rest/api/space?limit=1"
        response = requests.get(
            url,
            auth=(username, api_token),
            headers={{"Accept": "application/json"}},
            timeout=10
        )
        
        # Check status code
        if response.status_code != 200:
            return False, f"Connection test failed: HTTP {{response.status_code}} - {{response.text}}"
        
        # Check if the response is empty
        if not response.text.strip():
            return False, "Empty response from Confluence API. Please check your credentials and URL."
        
        # Check if the response is valid JSON
        try:
            data = response.json()
            
            # Check for error messages
            if "message" in data:
                return False, f"Confluence API error: {{data['message']}}"
            
            return True, "Connection successful"
        except ValueError as e:
            return False, f"Invalid JSON response from Confluence API: {{e}}. Raw response: {{response.text[:100]}}..."
    except requests.exceptions.RequestException as e:
        return False, f"Connection test error: {{str(e)}}"
    except Exception as e:
        return False, f"Unexpected error: {{str(e)}}"

def make_api_request(url: str, auth_tuple: Tuple[str, str]) -> Optional[str]:
    try:
        response = requests.get(
            url,
            auth=auth_tuple,
            headers={{"Accept": "application/json"}},
            timeout=10
        )
        
        if response.status_code != 200:
            logger.error(f"API request error: HTTP {{response.status_code}} - {{response.text}}")
            return None
        
        return response.text
    except requests.exceptions.RequestException as e:
        logger.error(f"API request error: {{str(e)}}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error: {{str(e)}}")
        return None

# Get space content
def get_space_content(space_key: str) -> Optional[Dict[str, Any]]:
    confluence_url = os.environ.get("CONFLUENCE_URL", "").rstrip('/')
    username = os.environ.get("CONFLUENCE_USERNAME", "")
    api_token = os.environ.get("CONFLUENCE_API_TOKEN", "")
    
    # Build the URL with a higher limit (max is 100 per request)
    content_url = f"{{confluence_url}}/rest/api/space/{{space_key}}/content?limit=100"
    
    logger.info(f"Fetching content from space '{{space_key}}' at URL: {{content_url}}")
    
    # Make the API request
    result = make_api_request(content_url, (username, api_token))
    if not result:
        return None
    
    try:
        data = json.loads(result)
        
        # Check if we need to paginate for more results
        all_pages = []
        all_blogs = []
        
        # Add initial results
        if "page" in data and "results" in data["page"]:
            all_pages.extend(data["page"]["results"])
            
        if "blogpost" in data and "results" in data["blogpost"]:
            all_blogs.extend(data["blogpost"]["results"])
        
        # Handle pagination for pages if needed
        if "page" in data and "_links" in data["page"] and "next" in data["page"]["_links"]:
            logger.info("More than 100 pages found, retrieving additional pages...")
            next_url = data["page"]["_links"]["next"]
            while next_url:
                full_next_url = f"{{confluence_url}}{{next_url}}"
                logger.info(f"Fetching next page batch from: {{full_next_url}}")
                next_result = make_api_request(full_next_url, (username, api_token))
                if not next_result:
                    break
                    
                try:
                    next_data = json.loads(next_result)
                    if "results" in next_data:
                        all_pages.extend(next_data["results"])
                        
                    # Check if there are more pages
                    if "_links" in next_data and "next" in next_data["_links"]:
                        next_url = next_data["_links"]["next"]
                    else:
                        next_url = None
                except json.JSONDecodeError:
                    logger.error("Error parsing paginated response")
                    next_url = None
        
        # Handle pagination for blogs if needed
        if "blogpost" in data and "_links" in data["blogpost"] and "next" in data["blogpost"]["_links"]:
            logger.info("More than 100 blog posts found, retrieving additional blog posts...")
            next_url = data["blogpost"]["_links"]["next"]
            while next_url:
                full_next_url = f"{{confluence_url}}{{next_url}}"
                logger.info(f"Fetching next blog batch from: {{full_next_url}}")
                next_result = make_api_request(full_next_url, (username, api_token))
                if not next_result:
                    break
                    
                try:
                    next_data = json.loads(next_result)
                    if "results" in next_data:
                        all_blogs.extend(next_data["results"])
                        
                    # Check if there are more blogs
                    if "_links" in next_data and "next" in next_data["_links"]:
                        next_url = next_data["_links"]["next"]
                    else:
                        next_url = None
                except json.JSONDecodeError:
                    logger.error("Error parsing paginated response")
                    next_url = None
        
        # Update the data with all pages and blogs
        if all_pages:
            if "page" not in data:
                data["page"] = {{}}
            data["page"]["results"] = all_pages
            data["page"]["size"] = len(all_pages)
            
        if all_blogs:
            if "blogpost" not in data:
                data["blogpost"] = {{}}
            data["blogpost"]["results"] = all_blogs
            data["blogpost"]["size"] = len(all_blogs)
            
        logger.info(f"Total pages retrieved: {{len(all_pages)}}, Total blogs retrieved: {{len(all_blogs)}}")
        return data
        
    except json.JSONDecodeError:
        logger.error("Error parsing response from Confluence API")
        return None

# Get page content
def get_page_content(page_id: str) -> Optional[Dict[str, str]]:
    confluence_url = os.environ.get("CONFLUENCE_URL", "").rstrip('/')
    username = os.environ.get("CONFLUENCE_USERNAME", "")
    api_token = os.environ.get("CONFLUENCE_API_TOKEN", "")
    
    url = f"{{confluence_url}}/rest/api/content/{{page_id}}?expand=body.storage"
    
    result = make_api_request(url, (username, api_token))
    if not result:
        return None
    
    try:
        data = json.loads(result)
        return {{
            "id": data.get("id"),
            "title": data.get("title"),
            "content": data.get("body", {{}}).get("storage", {{}}).get("value", ""),
            "url": f"{{confluence_url}}/pages/viewpage.action?pageId={{page_id}}"
        }}
    except json.JSONDecodeError:
        logger.error("Error parsing page content response")
        return None

# Process content with LLM
def process_with_llm(pages: List[Dict[str, str]], user_query: str) -> str:
    if not pages:
        return "No content found to process."
    
    # Set up LLM
    litellm.request_timeout = 30
    litellm.num_retries = 3
    
    # Process each page
    all_results = []
    
    for page in pages:
        page_id = page.get("id")
        page_title = page.get("title")
        page_content = page.get("content", "")
        page_url = page.get("url", "")
        
        if not page_content:
            continue
        
        logger.info(f"Processing page: {{page_title}} (ID: {{page_id}})")
        
        # Chunk the content if needed
        chunks = chunk_content(page_content)
        page_results = []
        
        for i, chunk in enumerate(chunks):
            # Create prompt for this chunk
            prompt = (
                f"You are analyzing Confluence page content to answer a user query.\\n\\n"
                f"Page Title: {{page_title}}\\n"
                f"Page URL: {{page_url}}\\n\\n"
                f"User Query: {{user_query}}\\n\\n"
                f"Content (Chunk {{i+1}}/{{len(chunks)}}):\\n{{chunk}}\\n\\n"
                f"Based on this content, provide a concise answer to the user's query. "
                f"If this chunk doesn't contain relevant information, indicate that briefly."
            )
            
            messages = [
                {{"role": "system", "content": "You are a helpful assistant that analyzes Confluence content."}},
                {{"role": "user", "content": prompt}}
            ]
            
            try:
                response = litellm.completion(
                    messages=messages,
                    model="openai/Llama-4-Scout",
                    api_key=os.environ.get("LLM_API_KEY", ""),
                    base_url=os.environ.get("LLM_BASE_URL", ""),
                    stream=False,
                    user=os.environ.get("KUBIYA_USER_EMAIL", ""),
                    max_tokens=2048,
                    temperature=0.7,
                    top_p=0.1,
                    presence_penalty=0.0,
                    frequency_penalty=0.0,
                    timeout=30,
                )
                
                chunk_result = response.choices[0].message.content.strip()
                
                # Only add non-empty and relevant results
                if chunk_result and not chunk_result.lower().startswith("this chunk doesn't contain"):
                    page_results.append({{
                        "chunk": i+1,
                        "result": chunk_result
                    }})
                
            except Exception as e:
                logger.error(f"Error processing chunk {{i+1}}: {{str(e)}}")
                page_results.append({{
                    "chunk": i+1,
                    "result": f"Error processing this chunk: {{str(e)}}"
                }})
        
        # Summarize the page results
        if page_results:
            all_results.append({{
                "page_title": page_title,
                "page_url": page_url,
                "results": page_results
            }})
    
    # If we have results from multiple pages, summarize them
    if len(all_results) > 1:
        # Create a summary of all page results
        summary_prompt = (
            f"You've analyzed multiple Confluence pages to answer this query: '{{user_query}}'\\n\\n"
            "Here are the key findings from each page:\\n\\n"
        )
        
        for page_result in all_results:
            summary_prompt += f"Page: {{page_result['page_title']}}\\n"
            summary_prompt += f"URL: {{page_result['page_url']}}\\n"
            summary_prompt += "Key points:\\n"
            
            for chunk_result in page_result['results']:
                summary_prompt += f"- {{chunk_result['result']}}\\n"
            
            summary_prompt += "\\n"
        
        summary_prompt += (
            "Based on all this information, provide a comprehensive answer to the user's query. "
            "Include references to specific pages where the information was found."
        )
        
        messages = [
            {{"role": "system", "content": "You are a helpful assistant that synthesizes information from multiple sources."}},
            {{"role": "user", "content": summary_prompt}}
        ]
        
        try:
            response = litellm.completion(
                messages=messages,
                model="openai/Llama-4-Scout",
                api_key=os.environ.get("LLM_API_KEY", ""),
                base_url=os.environ.get("LLM_BASE_URL", ""),
                stream=False,
                user=os.environ.get("KUBIYA_USER_EMAIL", ""),
                max_tokens=2048,
                temperature=0.7,
                top_p=0.1,
                presence_penalty=0.0,
                frequency_penalty=0.0,
                timeout=30,
            )
            
            final_answer = response.choices[0].message.content.strip()
            return final_answer
            
        except Exception as e:
            logger.error(f"Error creating summary: {{str(e)}}")
            # Fall back to returning individual page results
            final_answer = f"Error creating summary: {{str(e)}}\\n\\nHere are the individual page results:\\n\\n"
            
            for page_result in all_results:
                final_answer += f"## {{page_result['page_title']}}\\n"
                final_answer += f"URL: {{page_result['page_url']}}\\n\\n"
                
                for chunk_result in page_result['results']:
                    final_answer += f"### Chunk {{chunk_result['chunk']}}:\\n{{chunk_result['result']}}\\n\\n"
            
            return final_answer
    
    # If we only have one page with results
    elif len(all_results) == 1:
        page_result = all_results[0]
        
        if len(page_result['results']) == 1:
            # If there's only one chunk result, return it directly
            return f"# {{page_result['page_title']}}\\n\\n{{page_result['results'][0]['result']}}\\n\\nSource: {{page_result['page_url']}}"
        else:
            # If there are multiple chunks, summarize them
            summary_prompt = (
                f"You've analyzed the Confluence page '{{page_result['page_title']}}' to answer this query: '{{user_query}}'\\n\\n"
                "Here are the key findings from different sections of the page:\\n\\n"
            )
            
            for chunk_result in page_result['results']:
                summary_prompt += f"Section {{chunk_result['chunk']}}:\\n{{chunk_result['result']}}\\n\\n"
            
            summary_prompt += (
                "Based on all this information, provide a comprehensive answer to the user's query."
            )
            
            messages = [
                {{"role": "system", "content": "You are a helpful assistant that synthesizes information from multiple sections of a document."}},
                {{"role": "user", "content": summary_prompt}}
            ]
            
            try:
                response = litellm.completion(
                    messages=messages,
                    model="openai/Llama-4-Scout",
                    api_key=os.environ.get("LLM_API_KEY", ""),
                    base_url=os.environ.get("LLM_BASE_URL", ""),
                    stream=False,
                    user=os.environ.get("KUBIYA_USER_EMAIL", ""),
                    max_tokens=2048,
                    temperature=0.7,
                    top_p=0.1,
                    presence_penalty=0.0,
                    frequency_penalty=0.0,
                    timeout=30,
                )
                
                final_answer = response.choices[0].message.content.strip()
                return f"# {{page_result['page_title']}}\\n\\n{{final_answer}}\\n\\nSource: {{page_result['page_url']}}"
                
            except Exception as e:
                logger.error(f"Error creating page summary: {{str(e)}}")
                # Fall back to returning individual chunk results
                final_answer = f"# {{page_result['page_title']}}\\n\\nError creating summary: {{str(e)}}\\n\\nHere are the individual section results:\\n\\n"
                
                for chunk_result in page_result['results']:
                    final_answer += f"## Section {{chunk_result['chunk']}}:\\n{{chunk_result['result']}}\\n\\n"
                
                final_answer += f"\\nSource: {{page_result['page_url']}}"
                return final_answer
    
    return "No relevant information found in the space content."

# Chunk content into manageable pieces
def chunk_content(content: str, max_size: int = 8000) -> List[str]:
    if len(content) <= max_size:
        return [content]
    
    # Try to split at paragraph boundaries
    paragraphs = content.split('\\n\\n')
    chunks = []
    current_chunk = ""
    
    for para in paragraphs:
        if len(current_chunk) + len(para) + 2 <= max_size:
            if current_chunk:
                current_chunk += '\\n\\n'
            current_chunk += para
        else:
            if current_chunk:
                chunks.append(current_chunk)
            
            # If a single paragraph is too large, split it further
            if len(para) > max_size:
                # Split at sentence boundaries
                sentences = para.replace('. ', '.\\n').split('\\n')
                current_chunk = ""
                
                for sentence in sentences:
                    if len(current_chunk) + len(sentence) + 1 <= max_size:
                        if current_chunk:
                            current_chunk += ' '
                        current_chunk += sentence
                    else:
                        if current_chunk:
                            chunks.append(current_chunk)
                        
                        # If a single sentence is too large, just split it
                        if len(sentence) > max_size:
                            for i in range(0, len(sentence), max_size):
                                chunks.append(sentence[i:i+max_size])
                            current_chunk = ""
                        else:
                            current_chunk = sentence
            else:
                current_chunk = para
    
    if current_chunk:
        chunks.append(current_chunk)
    
    return chunks

def execute_confluence_action(**kwargs) -> Dict[str, Any]:
    logger.info(f"Executing Confluence space content analyzer with params: {{kwargs}}")
    
    # Validate connection
    valid, message = validate_confluence_connection()
    if not valid:
        return {{"success": False, "error": message}}
    
    space_key = kwargs.get('space_key')
    query = kwargs.get('query', '')
    
    if not space_key:
        return {{"success": False, "error": "Space key is required"}}
    
    # Get space content
    logger.info(f"Retrieving content from space: {{space_key}}")
    content_result = get_space_content(space_key)
    
    if not content_result:
        return {{"success": False, "error": f"Failed to retrieve content from space: {{space_key}}"}}
    
    # Check if we got any results
    page_count = content_result.get("page", {{}}).get("size", 0)
    blog_count = content_result.get("blogpost", {{}}).get("size", 0)
    
    logger.info(f"Found {{page_count}} pages and {{blog_count}} blog posts in space '{{space_key}}'")
    
    if page_count == 0 and blog_count == 0:
        return {{"success": True, "message": f"No content found in space: {{space_key}}"}}
    
    # Log details about each page found
    if page_count > 0:
        logger.info("Pages found in the space:")
        for idx, page in enumerate(content_result.get("page", {{}}).get("results", []), 1):
            page_id = page.get("id", "unknown")
            page_title = page.get("title", "untitled")
            logger.info(f"  {{idx}}. Page ID: {{page_id}}, Title: {{page_title}}")
    
    # Log details about each blog post found
    if blog_count > 0:
        logger.info("Blog posts found in the space:")
        for idx, blog in enumerate(content_result.get("blogpost", {{}}).get("results", []), 1):
            blog_id = blog.get("id", "unknown")
            blog_title = blog.get("title", "untitled")
            logger.info(f"  {{idx}}. Blog ID: {{blog_id}}, Title: {{blog_title}}")
    
    # If no query, just return the content list
    if not query:
        result = {{"success": True, "space_key": space_key}}
        
        # Format pages
        if page_count > 0:
            pages = []
            for page in content_result.get("page", {{}}).get("results", []):
                pages.append({{
                    "id": page.get("id"),
                    "title": page.get("title"),
                    "type": page.get("type"),
                    "url": f"{{os.environ.get('CONFLUENCE_URL', '').rstrip('/')}}/display/{{space_key}}/{{page.get('id')}}"
                }})
            result["pages"] = pages
            result["page_count"] = page_count
        
        # Format blog posts
        if blog_count > 0:
            blogs = []
            for blog in content_result.get("blogpost", {{}}).get("results", []):
                blogs.append({{
                    "id": blog.get("id"),
                    "title": blog.get("title"),
                    "type": blog.get("type"),
                    "url": f"{{os.environ.get('CONFLUENCE_URL', '').rstrip('/')}}/display/{{space_key}}/{{blog.get('id')}}"
                }})
            result["blogs"] = blogs
            result["blog_count"] = blog_count
        
        return result
    else:
        # Process with query
        logger.info(f"Processing query: {{query}}")
        
        # Get full content of each page
        pages = []
        
        # Extract page IDs and titles
        if "page" in content_result and "results" in content_result["page"]:
            logger.info("Fetching full content for each page:")
            for idx, page in enumerate(content_result["page"]["results"], 1):
                page_id = page.get("id")
                page_title = page.get("title", "untitled")
                if page_id:
                    logger.info(f"  {{idx}}. Fetching content for page: {{page_title}} (ID: {{page_id}})")
                    page_content = get_page_content(page_id)
                    if page_content:
                        logger.info(f"     ✓ Successfully retrieved content ({{len(page_content.get('content', ''))}} characters)")
                        pages.append(page_content)
                    else:
                        logger.warning(f"     ✗ Failed to retrieve content for page: {{page_title}}")
        
        # Process with LLM
        if not pages:
            return {{"success": True, "message": "No page content found to process"}}
        
        logger.info(f"Processing {{len(pages)}} pages with LLM for query: '{{query}}'")
        result = process_with_llm(pages, query)
        logger.info("LLM processing completed successfully")
        return {{"success": True, "answer": result}}

if __name__ == "__main__":
    # Check for required environment variables
    if not os.environ.get("CONFLUENCE_URL") or not os.environ.get("CONFLUENCE_USERNAME") or not os.environ.get("CONFLUENCE_API_TOKEN"):
        logger.error("Confluence credentials not properly configured")
        print(json.dumps({{"success": False, "error": "Confluence credentials not properly configured"}}))
        sys.exit(1)

    logger.info("Starting Confluence space content analyzer...")
    
    # Get arguments from environment variables
    args = {{}}
    for arg in {arg_names_json}:
        if arg in os.environ:
            args[arg] = os.environ[arg]
    
    result = execute_confluence_action(**args)
    logger.info("Confluence space content analyzer completed")
    print(json.dumps(result))
"""
        
        super().__init__(
            name=name,
            description=description,
            icon_url=CONFLUENCE_ICON_URL,
            type="docker",
            image="python:3.11-slim",
            content="apt-get update -qq >/dev/null 2>&1 && apt-get install -qq -y curl >/dev/null 2>&1 && pip install -q requests litellm >/dev/null 2>&1 && python3 /tmp/space_content_analyzer.py",
            args=args,
            env=env,
            secrets=secrets,
            with_files=[
                FileSpec(
                    destination="/tmp/space_content_analyzer.py",
                    content=script_content
                )
            ],
            mermaid=mermaid_diagram,
            long_running=True
        )

class ConfluenceToKnowledgeTool(Tool):
    """Base class for importing Confluence content to Kubiya knowledge."""
    
    def __init__(self, name, description, args):
        # Shell script to set up the environment and run the Python script
        shell_script = """
#!/bin/bash
set -e

# Install required packages
apt-get update -qq >/dev/null 2>&1
apt-get install -qq -y curl python3 python3-pip jq file >/dev/null 2>&1
pip3 install --quiet requests >/dev/null 2>&1

# Download Kubiya CLI with proper error handling
echo "Downloading Kubiya CLI..."
CLI_URL="https://github.com/kubiyabot/cli/releases/download/v1.0.14/kubiya-cli-linux-amd64"
CLI_PATH="/usr/local/bin/kubiya"

# Create a temporary file for downloading
TMP_CLI_PATH="/tmp/kubiya-cli"

# Download with curl, showing progress and handling errors
if ! curl -L "$CLI_URL" -o "$TMP_CLI_PATH" --fail --silent --show-error; then
    echo "Failed to download Kubiya CLI from $CLI_URL"
    exit 1
fi

# Move to final location and make executable
mv "$TMP_CLI_PATH" "$CLI_PATH"
chmod +x "$CLI_PATH"

# Verify the CLI was installed correctly
if [ ! -x "$CLI_PATH" ]; then
    echo "Error: Kubiya CLI was not installed correctly at $CLI_PATH"
    exit 1
fi

echo "Kubiya CLI installed successfully at $CLI_PATH"
ls -la "$CLI_PATH"
file "$CLI_PATH"

# Test the CLI
echo "Testing Kubiya CLI..."
"$CLI_PATH" --help || echo "CLI help command failed, but continuing..."

# Run the Python script (now provided as a file spec)
python3 /tmp/import_confluence.py
"""
        
        # Python script for importing Confluence content to Kubiya knowledge
        python_script = """
import os
import sys
import json
import logging
import requests
import tempfile
import subprocess
from typing import Dict, List, Any, Optional

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def validate_confluence_connection():
    confluence_url = os.environ.get("CONFLUENCE_URL", "")
    username = os.environ.get("CONFLUENCE_USERNAME", "")
    api_token = os.environ.get("CONFLUENCE_API_TOKEN", "")
    
    if not confluence_url or not username or not api_token:
        logger.error("Confluence credentials not properly configured")
        return False
    
    # Test the connection
    try:
        url = f"{confluence_url.rstrip('/')}/rest/api/space?limit=1"
        response = requests.get(
            url,
            auth=(username, api_token),
            headers={"Accept": "application/json"},
            timeout=10
        )
        
        # Check status code
        if response.status_code != 200:
            logger.error(f"Connection test failed: HTTP {response.status_code} - {response.text}")
            return False
        
        # Check if the response is valid JSON
        try:
            data = response.json()
            
            # Check for error messages
            if "message" in data:
                logger.error(f"Confluence API error: {data['message']}")
                return False
            
            logger.info("Confluence connection successful")
            return True
        except ValueError as e:
            logger.error(f"Invalid JSON response from Confluence API: {e}")
            return False
    except requests.exceptions.RequestException as e:
        logger.error(f"Connection test error: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return False

def make_api_request(url, auth_tuple):
    try:
        response = requests.get(
            url,
            auth=auth_tuple,
            headers={"Accept": "application/json"},
            timeout=10
        )
        
        if response.status_code != 200:
            logger.error(f"API request error: HTTP {response.status_code} - {response.text}")
            return None
        
        return response.text
    except Exception as e:
        logger.error(f"API request error: {str(e)}")
        return None

def get_space_content(space_key):
    confluence_url = os.environ.get("CONFLUENCE_URL", "").rstrip('/')
    username = os.environ.get("CONFLUENCE_USERNAME", "")
    api_token = os.environ.get("CONFLUENCE_API_TOKEN", "")
    
    # Build the URL with a higher limit (max is 100 per request)
    content_url = f"{confluence_url}/rest/api/space/{space_key}/content?limit=100"
    
    logger.info(f"Fetching content from space '{space_key}' at URL: {content_url}")
    
    # Make the API request
    result = make_api_request(content_url, (username, api_token))
    if not result:
        return None
    
    try:
        data = json.loads(result)
        
        # Check if we need to paginate for more results
        all_pages = []
        all_blogs = []
        
        # Add initial results
        if "page" in data and "results" in data["page"]:
            all_pages.extend(data["page"]["results"])
            
        if "blogpost" in data and "results" in data["blogpost"]:
            all_blogs.extend(data["blogpost"]["results"])
        
        # Handle pagination for pages if needed
        if "page" in data and "_links" in data["page"] and "next" in data["page"]["_links"]:
            logger.info("More than 100 pages found, retrieving additional pages...")
            next_url = data["page"]["_links"]["next"]
            while next_url:
                full_next_url = f"{confluence_url}{next_url}"
                logger.info(f"Fetching next page batch from: {full_next_url}")
                next_result = make_api_request(full_next_url, (username, api_token))
                if not next_result:
                    break
                    
                try:
                    next_data = json.loads(next_result)
                    if "results" in next_data:
                        all_pages.extend(next_data["results"])
                        
                    # Check if there are more pages
                    if "_links" in next_data and "next" in next_data["_links"]:
                        next_url = next_data["_links"]["next"]
                    else:
                        next_url = None
                except json.JSONDecodeError:
                    logger.error("Error parsing paginated response")
                    next_url = None
        
        # Handle pagination for blogs if needed
        if "blogpost" in data and "_links" in data["blogpost"] and "next" in data["blogpost"]["_links"]:
            logger.info("More than 100 blog posts found, retrieving additional blog posts...")
            next_url = data["blogpost"]["_links"]["next"]
            while next_url:
                full_next_url = f"{confluence_url}{next_url}"
                logger.info(f"Fetching next blog batch from: {full_next_url}")
                next_result = make_api_request(full_next_url, (username, api_token))
                if not next_result:
                    break
                    
                try:
                    next_data = json.loads(next_result)
                    if "results" in next_data:
                        all_blogs.extend(next_data["results"])
                        
                    # Check if there are more blogs
                    if "_links" in next_data and "next" in next_data["_links"]:
                        next_url = next_data["_links"]["next"]
                    else:
                        next_url = None
                except json.JSONDecodeError:
                    logger.error("Error parsing paginated response")
                    next_url = None
        
        # Update the data with all pages and blogs
        if all_pages:
            if "page" not in data:
                data["page"] = {}
            data["page"]["results"] = all_pages
            data["page"]["size"] = len(all_pages)
            
        if all_blogs:
            if "blogpost" not in data:
                data["blogpost"] = {}
            data["blogpost"]["results"] = all_blogs
            data["blogpost"]["size"] = len(all_blogs)
            
        logger.info(f"Total pages retrieved: {len(all_pages)}, Total blogs retrieved: {len(all_blogs)}")
        return data
        
    except json.JSONDecodeError:
        logger.error("Error parsing response from Confluence API")
        return None

def get_page_content(page_id):
    confluence_url = os.environ.get("CONFLUENCE_URL", "").rstrip('/')
    username = os.environ.get("CONFLUENCE_USERNAME", "")
    api_token = os.environ.get("CONFLUENCE_API_TOKEN", "")
    
    url = f"{confluence_url}/rest/api/content/{page_id}?expand=body.storage,metadata.labels"
    
    result = make_api_request(url, (username, api_token))
    if not result:
        return None
    
    try:
        data = json.loads(result)
        
        # Extract labels
        labels = []
        if "metadata" in data and "labels" in data["metadata"] and "results" in data["metadata"]["labels"]:
            for label in data["metadata"]["labels"]["results"]:
                if "name" in label:
                    labels.append(label["name"])
        
        return {
            "id": data.get("id"),
            "title": data.get("title"),
            "content": data.get("body", {}).get("storage", {}).get("value", ""),
            "url": f"{confluence_url}/pages/viewpage.action?pageId={page_id}",
            "labels": ",".join(labels)
        }
    except json.JSONDecodeError:
        logger.error("Error parsing page content response")
        return None

def create_knowledge_item(title, content, labels, space_key):
    try:
        # Create a temporary file with .md extension
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.md') as temp_file:
            temp_file.write(content)
            content_file_path = temp_file.name
        
        # Prepare labels with confluence space key
        if labels:
            all_labels = f"{labels},confluence,space-{space_key}"
        else:
            all_labels = f"confluence,space-{space_key}"
        
        # Log the full API key for debugging
        api_key = os.environ.get("KUBIYA_API_KEY", "")
        if not api_key:
            logger.error("KUBIYA_API_KEY environment variable is not set")
            return None
        else:
            logger.info(f"Using KUBIYA_API_KEY: {api_key}")
        
        # Create a shell command matching the example format
        shell_cmd = f'/usr/local/bin/kubiya knowledge create --name "{title}" --desc "Imported from Confluence space: {space_key}" --labels {all_labels} --content-file {content_file_path}'
        
        logger.info(f"Running shell command: {shell_cmd}")
        logger.info(f"Content file size: {os.path.getsize(content_file_path)} bytes")
        logger.info(f"Content file path: {content_file_path}")
        
        # Try with verbose output
        os.environ["KUBIYA_DEBUG"] = "true"
        
        # Execute the shell command
        result = subprocess.run(shell_cmd, shell=True, capture_output=True, text=True)
        
        # Clean up the temporary file
        os.unlink(content_file_path)
        
        if result.returncode != 0:
            logger.error(f"Error creating knowledge item: {result.stderr}")
            logger.error(f"Command output: {result.stdout}")
            return None
        
        return result.stdout.strip()
    except Exception as e:
        logger.error(f"Error creating knowledge item: {str(e)}")
        return None

def main():
    # Check for required environment variables
    if not validate_confluence_connection():
        print(json.dumps({"success": False, "error": "Confluence connection failed"}))
        sys.exit(1)
    
    # Get arguments from environment variables
    space_key = os.environ.get("space_key", "")
    include_blogs = os.environ.get("include_blogs", "true").lower() == "true"
    
    if not space_key:
        print(json.dumps({"success": False, "error": "space_key is required"}))
        sys.exit(1)
    
    # Get space content
    content_result = get_space_content(space_key)
    
    if not content_result:
        print(json.dumps({"success": False, "error": f"Failed to retrieve content from space: {space_key}"}))
        sys.exit(1)
    
    # Check if we got any results
    page_count = content_result.get("page", {}).get("size", 0)
    blog_count = content_result.get("blogpost", {}).get("size", 0)
    
    logger.info(f"Found {page_count} pages and {blog_count} blog posts in space '{space_key}'")
    
    if page_count == 0 and blog_count == 0:
        print(json.dumps({"success": True, "message": f"No content found in space: {space_key}"}))
        sys.exit(0)
    
    # Process pages
    imported_count = 0
    failed_count = 0
    
    if page_count > 0:
        logger.info(f"Importing {page_count} pages from space '{space_key}'...")
        
        for idx, page in enumerate(content_result.get("page", {}).get("results", []), 1):
            page_id = page.get("id")
            page_title = page.get("title", "untitled")
            
            if page_id:
                logger.info(f"[{idx}/{page_count}] Processing page: {page_title} (ID: {page_id})")
                page_data = get_page_content(page_id)
                
                if page_data and page_data.get("content"):
                    # Create knowledge item
                    result = create_knowledge_item(
                        page_data["title"],
                        page_data["content"],
                        page_data["labels"],
                        space_key
                    )
                    
                    if result:
                        try:
                            result_json = json.loads(result)
                            if "uuid" in result_json:
                                logger.info(f"✅ Successfully imported page '{page_title}' as knowledge item with UUID: {result_json['uuid']}")
                                imported_count += 1
                            else:
                                logger.error(f"❌ Failed to import page '{page_title}': {result}")
                                failed_count += 1
                        except json.JSONDecodeError:
                            logger.error(f"❌ Failed to import page '{page_title}': Invalid response format")
                            failed_count += 1
                    else:
                        logger.error(f"❌ Failed to import page '{page_title}'")
                        failed_count += 1
                else:
                    logger.error(f"❌ Failed to retrieve content for page '{page_title}'")
                    failed_count += 1
    
    # Process blog posts if requested
    if include_blogs and blog_count > 0:
        logger.info(f"Importing {blog_count} blog posts from space '{space_key}'...")
        
        for idx, blog in enumerate(content_result.get("blogpost", {}).get("results", []), 1):
            blog_id = blog.get("id")
            blog_title = blog.get("title", "untitled")
            
            if blog_id:
                logger.info(f"[{idx}/{blog_count}] Processing blog post: {blog_title} (ID: {blog_id})")
                blog_data = get_page_content(blog_id)
                
                if blog_data and blog_data.get("content"):
                    # Create knowledge item with blog label
                    labels = blog_data["labels"]
                    if labels:
                        labels += ",blog"
                    else:
                        labels = "blog"
                    
                    result = create_knowledge_item(
                        blog_data["title"],
                        blog_data["content"],
                        labels,
                        space_key
                    )
                    
                    if result:
                        try:
                            result_json = json.loads(result)
                            if "uuid" in result_json:
                                logger.info(f"✅ Successfully imported blog post '{blog_title}' as knowledge item with UUID: {result_json['uuid']}")
                                imported_count += 1
                            else:
                                logger.error(f"❌ Failed to import blog post '{blog_title}': {result}")
                                failed_count += 1
                        except json.JSONDecodeError:
                            logger.error(f"❌ Failed to import blog post '{blog_title}': Invalid response format")
                            failed_count += 1
                    else:
                        logger.error(f"❌ Failed to import blog post '{blog_title}'")
                        failed_count += 1
                else:
                    logger.error(f"❌ Failed to retrieve content for blog post '{blog_title}'")
                    failed_count += 1
    
    # Print summary
    summary = {
        "success": True,
        "space_key": space_key,
        "total_content_items": page_count + (blog_count if include_blogs else 0),
        "imported_count": imported_count,
        "failed_count": failed_count
    }
    
    print(json.dumps(summary))

if __name__ == "__main__":
    main()
"""
        
        super().__init__(
            name=name,
            description=description,
            icon_url=CONFLUENCE_ICON_URL,
            type="docker",
            image="python:3.9-slim",  # Changed from Alpine to Debian-based image
            content=shell_script,
            args=args,
            env=["CONFLUENCE_URL", "CONFLUENCE_USERNAME", "KUBIYA_API_KEY"],
            secrets=["CONFLUENCE_API_TOKEN"],
            with_files=[
                FileSpec(
                    destination="/tmp/import_confluence.py",
                    content=python_script
                )
            ]
        )
