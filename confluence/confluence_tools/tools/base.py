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
import re
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
    
    # First, chunk each page individually
    all_chunks = []
    logger.info(f"Preparing {{len(pages)}} pages for processing")
    
    for page_idx, page in enumerate(pages, 1):
        page_id = page.get("id")
        page_title = page.get("title")
        page_content = page.get("content", "")
        page_url = page.get("url", "")
        
        if not page_content:
            continue
        
        # Chunk this page's content
        page_chunks = chunk_content(page_content)
        logger.info(f"Page {{page_idx}}/{{len(pages)}}: '{{page_title}}' split into {{len(page_chunks)}} chunks")
        
        # Add metadata to each chunk
        for i, chunk in enumerate(page_chunks):
            all_chunks.append({{
                "page_id": page_id,
                "page_title": page_title,
                "page_url": page_url,
                "chunk_num": i+1,
                "total_chunks": len(page_chunks),
                "content": chunk
            }})
    
    # Now process chunks in batches
    batch_size = 3  # Process 3 chunks at a time
    total_chunks = len(all_chunks)
    logger.info(f"Total chunks across all pages: {{total_chunks}}")
    
    all_results = []
    
    for batch_start in range(0, total_chunks, batch_size):
        batch_end = min(batch_start + batch_size, total_chunks)
        current_batch = all_chunks[batch_start:batch_end]
        
        logger.info(f"Processing batch {{batch_start//batch_size + 1}}/{{(total_chunks + batch_size - 1)//batch_size}}: chunks {{batch_start+1}}-{{batch_end}}")
        
        # Combine chunks into a single prompt
        combined_content = ""
        batch_metadata = []
        
        for chunk_data in current_batch:
            # Add chunk metadata and content
            combined_content += f"\\n\\n--- PAGE: {{chunk_data['page_title']}} (Chunk {{chunk_data['chunk_num']}}/{{chunk_data['total_chunks']}}) ---\\n\\n{{chunk_data['content']}}"
            batch_metadata.append({{
                "page_id": chunk_data["page_id"],
                "page_title": chunk_data["page_title"],
                "page_url": chunk_data["page_url"],
                "chunk_num": chunk_data["chunk_num"],
                "total_chunks": chunk_data["total_chunks"]
            }})
        
        # Process this batch with the LLM
        prompt = (
            f"You are analyzing content from multiple Confluence pages to answer a user query.\\n\\n"
            f"User Query: {{user_query}}\\n\\n"
            f"Content from multiple pages:\\n{{combined_content}}\\n\\n"
            f"IMPORTANT INSTRUCTIONS:\\n"
            f"1. If this content contains information relevant to the query, provide a DETAILED and COMPREHENSIVE answer.\\n"
            f"2. Include ALL relevant details, examples, steps, or explanations from the content.\\n"
            f"3. Do not summarize excessively - preserve important details.\\n"
            f"4. Clearly specify which page(s) the information came from.\\n"
            f"5. If the content doesn't contain relevant information, briefly indicate that.\\n\\n"
            f"Your detailed response:"
        )
        
        messages = [
            {{"role": "system", "content": "You are a detail-oriented assistant that analyzes Confluence content. Your primary goal is to provide COMPREHENSIVE and DETAILED answers, preserving all relevant information from the source material. Never sacrifice important details for brevity."}},
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
                max_tokens=4096,  # Increased from 2048
                temperature=0.3,  # Lower temperature for more detailed/factual responses
                top_p=0.1,
                presence_penalty=0.0,
                frequency_penalty=0.0,
                timeout=45,  # Increased timeout for longer responses
            )
            
            chunk_result = response.choices[0].message.content.strip()
            
            # Process chunk results with detail level assessment
            if "no relevant information" not in chunk_result.lower() and "doesn't contain" not in chunk_result.lower():
                # Check how detailed the response is
                detail_level = len(chunk_result.split())
                
                if detail_level > 50:  # If response has more than 50 words
                    logger.info(f"  ✓ Found DETAILED relevant information in chunk {{batch_start+1}} ({{detail_level}} words)")
                    batch_results.append({{
                        "chunk": batch_start+1,
                        "result": chunk_result,
                        "detail_level": detail_level,
                        "page_info": current_batch[0]  # Use the first chunk's page info
                    }})
                else:
                    logger.info(f"  ⚠ Found BRIEF relevant information in chunk {{batch_start+1}} ({{detail_level}} words)")
                    batch_results.append({{
                        "chunk": batch_start+1,
                        "result": chunk_result,
                        "detail_level": detail_level,
                        "page_info": current_batch[0]
                    }})
            else:
                logger.info(f"  ✗ No relevant information in batch {{batch_start+1}}")
                
        except Exception as e:
            logger.error(f"Error processing batch {{batch_start+1}}: {{str(e)}}")
            batch_results.append({{
                "chunk": batch_start+1,
                "result": f"Error processing this batch: {{str(e)}}",
                "detail_level": 0,
                "page_info": current_batch[0] if current_batch else {{"page_title": "Unknown", "page_url": ""}}
            }})
    
    # Sort results by detail level
    all_results.sort(key=lambda x: x.get("detail_level", 0), reverse=True)
    
    # If we have results, create a comprehensive summary
    if all_results:
        # Use the most detailed results first in the summary
        detailed_findings = ""
        relevant_pages = []
        
        for result in all_results[:5]:  # Focus on top 5 most detailed results
            page_info = result.get("page_info", {{}})
            detailed_findings += f"From page '{{page_info.get('page_title', 'Unknown')}}':\\n{{result.get('result', '')}}\\n\\n"
            
            # Collect unique pages for references
            page_data = {{
                "title": page_info.get("page_title", "Unknown"),
                "url": page_info.get("page_url", "")
            }}
            if page_data not in relevant_pages:
                relevant_pages.append(page_data)
        
        # Create final summary
        summary_prompt = (
            f"You've analyzed multiple Confluence pages to answer this query: '{{user_query}}'\\n\\n"
            f"Here are the detailed findings from each relevant section:\\n\\n"
            f"{{detailed_findings}}\\n\\n"
            f"IMPORTANT INSTRUCTIONS:\\n"
            f"1. Provide a COMPREHENSIVE answer that includes ALL relevant details from the findings.\\n"
            f"2. Do not over-summarize or omit important information.\\n"
            f"3. Include specific examples, steps, code snippets, or explanations from the original content.\\n"
            f"4. Clearly reference which Confluence page(s) each piece of information came from.\\n"
            f"5. Format your response with clear sections and include the full URLs to relevant pages.\\n\\n"
            f"Your comprehensive response:"
        )
        
        messages = [
            {{"role": "system", "content": "You are a detail-oriented assistant that synthesizes information from multiple sources."}},
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
                max_tokens=4096,
                temperature=0.3,
                top_p=0.1,
                presence_penalty=0.0,
                frequency_penalty=0.0,
                timeout=45,
            )
            
            final_answer = response.choices[0].message.content.strip()
            
            # Format the final answer to include source links
            formatted_answer = format_final_answer(final_answer, relevant_pages)
            return formatted_answer
            
        except Exception as e:
            logger.error(f"Error creating summary: {{str(e)}}")
            # Fall back to returning the most detailed result
            if all_results:
                return f"Error creating summary: {{str(e)}}\\n\\nMost relevant information found:\\n\\n{{all_results[0].get('result', 'No details available')}}"
            else:
                return f"Error creating summary: {{str(e)}}\\n\\nNo relevant information was found."
    
    return "No relevant information found in the space content."

def format_final_answer(answer, relevant_pages):
    formatted_answer = answer
    
    # Add source links section if not already included
    if "Source" not in formatted_answer and "References" not in formatted_answer:
        formatted_answer += "\\n\\n## Sources\\n"
        for page in relevant_pages:
            formatted_answer += f"- [{{page['title']}}]({{page['url']}})\\n"
    
    return formatted_answer

def semantic_chunk_content(content, max_size=8000):
    # First try to split at major section boundaries (headers)
    sections = re.split(r'<h[1-3][^>]*>.*?</h[1-3]>', content)
    
    if len(sections) > 1:
        # We found headers to split on
        chunks = []
        current_chunk = ""
        
        # Reconstruct with headers
        headers = re.findall(r'(<h[1-3][^>]*>.*?</h[1-3]>)', content)
        
        # Interleave headers and sections
        for i, section in enumerate(sections):
            if i > 0 and i-1 < len(headers):
                header = headers[i-1]
            else:
                header = ""
                
            if len(current_chunk) + len(header) + len(section) <= max_size:
                current_chunk += header + section
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = header + section
                
        if current_chunk:
            chunks.append(current_chunk)
            
        return chunks
    else:
        # Fall back to regular chunking
        return chunk_content(content, max_size)

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

        # Sort results by detail level before summarizing
        all_results.sort(key=lambda x: sum([r["detail_level"] for r in x["results"]]), reverse=True)

        # Use the most detailed results first in the summary
        detailed_findings = ""
        for batch_result in all_results[:5]:  # Focus on top 5 most detailed batches
            for chunk_result in batch_result["results"]:
                detailed_findings += f"From page '{{chunk_result['page_info']['page_title']}}':\n{{chunk_result['result']}}\n\n"

        # In the final summary step:
        summary_prompt = (
            f"You've analyzed multiple Confluence pages to answer this query: '{{user_query}}'\\n\\n"
            f"Here are the detailed findings from each relevant section:\\n\\n"
            f"{{detailed_findings}}\\n\\n"
            f"IMPORTANT INSTRUCTIONS:\\n"
            f"1. Provide a COMPREHENSIVE answer that includes ALL relevant details from the findings.\\n"
            f"2. Do not over-summarize or omit important information.\\n"
            f"3. Include specific examples, steps, code snippets, or explanations from the original content.\\n"
            f"4. Clearly reference which Confluence page(s) each piece of information came from.\\n"
            f"5. Format your response with clear sections and include the full URLs to relevant pages.\\n\\n"
            f"Your comprehensive response:"
        )

        return {{"success": True, "answer": result}}

def format_final_answer(answer, relevant_pages):
    formatted_answer = answer
    
    # Add source links section if not already included
    if "Source" not in formatted_answer and "References" not in formatted_answer:
        formatted_answer += "\\n\\n## Sources\\n"
        for page in relevant_pages:
            formatted_answer += f"- [{{page['title']}}]({{page['url']}})\\n"
    
    return formatted_answer

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
