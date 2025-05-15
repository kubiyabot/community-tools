#!/usr/bin/env python3
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
    """Validate Confluence API connection using credentials from environment variables.
    
    Returns:
        Tuple[bool, str]: Success status and message
    """
    confluence_url = os.environ.get("CONFLUENCE_URL", "")
    username = os.environ.get("CONFLUENCE_USERNAME", "")
    api_token = os.environ.get("CONFLUENCE_API_TOKEN", "")
    
    if not confluence_url or not username or not api_token:
        return False, "Confluence credentials not properly configured"
    
    # Test the connection
    try:
        url = f"{confluence_url.rstrip('/')}/rest/api/space?limit=1"
        response = requests.get(
            url,
            auth=(username, api_token),
            headers={"Accept": "application/json"},
            timeout=10  # Add timeout for better error handling
        )
        
        # Check status code
        if response.status_code != 200:
            return False, f"Connection test failed: HTTP {response.status_code} - {response.text}"
        
        # Check if the response is empty
        if not response.text.strip():
            return False, "Empty response from Confluence API. Please check your credentials and URL."
        
        # Check if the response is valid JSON
        try:
            data = response.json()
            
            # Check for error messages
            if "message" in data:
                return False, f"Confluence API error: {data['message']}"
            
            return True, "Connection successful"
        except ValueError as e:
            return False, f"Invalid JSON response from Confluence API: {e}. Raw response: {response.text[:100]}..."
    except requests.exceptions.RequestException as e:
        return False, f"Connection test error: {str(e)}"
    except Exception as e:
        return False, f"Unexpected error: {str(e)}"

def make_api_request(url: str, auth_tuple: Tuple[str, str]) -> Optional[str]:
    """Make a GET request to the Confluence API.
    
    Args:
        url: The API endpoint URL
        auth_tuple: Tuple of (username, api_token)
        
    Returns:
        Optional[str]: Response text or None if request failed
    """
    try:
        response = requests.get(
            url,
            auth=auth_tuple,
            headers={"Accept": "application/json"},
            timeout=10  # Add timeout for better error handling
        )
        
        if response.status_code != 200:
            logger.error(f"API request error: HTTP {response.status_code} - {response.text}")
            return None
        
        return response.text
    except requests.exceptions.RequestException as e:
        logger.error(f"API request error: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return None

# Get space content
def get_space_content(space_key: str, limit: Optional[int] = None) -> Optional[Dict[str, Any]]:
    """Retrieve content from a Confluence space.
    
    Args:
        space_key: The key of the Confluence space
        limit: Optional limit on the number of results
        
    Returns:
        Optional[Dict[str, Any]]: JSON response data or None if request failed
    """
    confluence_url = os.environ.get("CONFLUENCE_URL", "").rstrip('/')
    username = os.environ.get("CONFLUENCE_USERNAME", "")
    api_token = os.environ.get("CONFLUENCE_API_TOKEN", "")
    
    # Build the URL
    content_url = f"{confluence_url}/rest/api/space/{space_key}/content"
    if limit:
        content_url += f"?limit={limit}"
    
    # Make the API request
    result = make_api_request(content_url, (username, api_token))
    if not result:
        return None
    
    try:
        return json.loads(result)
    except json.JSONDecodeError:
        logger.error("Error parsing response from Confluence API")
        return None

# Get page content
def get_page_content(page_id: str) -> Optional[Dict[str, str]]:
    """Retrieve the content of a specific Confluence page.
    
    Args:
        page_id: The ID of the Confluence page
        
    Returns:
        Optional[Dict[str, str]]: Page data or None if request failed
    """
    confluence_url = os.environ.get("CONFLUENCE_URL", "").rstrip('/')
    username = os.environ.get("CONFLUENCE_USERNAME", "")
    api_token = os.environ.get("CONFLUENCE_API_TOKEN", "")
    
    url = f"{confluence_url}/rest/api/content/{page_id}?expand=body.storage"
    
    result = make_api_request(url, (username, api_token))
    if not result:
        return None
    
    try:
        data = json.loads(result)
        return {
            "id": data.get("id"),
            "title": data.get("title"),
            "content": data.get("body", {}).get("storage", {}).get("value", ""),
            "url": f"{confluence_url}/pages/viewpage.action?pageId={page_id}"
        }
    except json.JSONDecodeError:
        logger.error("Error parsing page content response")
        return None

# Process content with LLM
def process_with_llm(pages: List[Dict[str, str]], user_query: str) -> str:
    """Process page content with LLM to answer user query.
    
    Args:
        pages: List of page data dictionaries
        user_query: The user's query to answer
        
    Returns:
        str: LLM-generated answer based on page content
    """
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
        
        logger.info(f"Processing page: {page_title} (ID: {page_id})")
        
        # Chunk the content if needed
        chunks = chunk_content(page_content)
        page_results = []
        
        for i, chunk in enumerate(chunks):
            # Create prompt for this chunk
            prompt = (
                f"You are analyzing Confluence page content to answer a user query.\n\n"
                f"Page Title: {page_title}\n"
                f"Page URL: {page_url}\n\n"
                f"User Query: {user_query}\n\n"
                f"Content (Chunk {i+1}/{len(chunks)}):\n{chunk}\n\n"
                f"Based on this content, provide a concise answer to the user's query. "
                f"If this chunk doesn't contain relevant information, indicate that briefly."
            )
            
            messages = [
                {"role": "system", "content": "You are a helpful assistant that analyzes Confluence content."},
                {"role": "user", "content": prompt}
            ]
            
            try:
                response = litellm.completion(
                    messages=messages,
                    model="openai/gpt-3.5-turbo",
                    api_key=os.environ.get("LLM_API_KEY", ""),
                    base_url=os.environ.get("LLM_BASE_URL", ""),
                    stream=False,
                    max_tokens=1000,
                    temperature=0.3,
                )
                
                chunk_result = response.choices[0].message.content.strip()
                
                # Only add non-empty and relevant results
                if chunk_result and not chunk_result.lower().startswith("this chunk doesn't contain"):
                    page_results.append({
                        "chunk": i+1,
                        "result": chunk_result
                    })
                
            except Exception as e:
                logger.error(f"Error processing chunk {i+1}: {str(e)}")
                page_results.append({
                    "chunk": i+1,
                    "result": f"Error processing this chunk: {str(e)}"
                })
        
        # Summarize the page results
        if page_results:
            all_results.append({
                "page_title": page_title,
                "page_url": page_url,
                "results": page_results
            })
    
    # If we have results from multiple pages, summarize them
    if len(all_results) > 1:
        # Create a summary of all page results
        summary_prompt = (
            f"You've analyzed multiple Confluence pages to answer this query: '{user_query}'\n\n"
            "Here are the key findings from each page:\n\n"
        )
        
        for page_result in all_results:
            summary_prompt += f"Page: {page_result['page_title']}\n"
            summary_prompt += f"URL: {page_result['page_url']}\n"
            summary_prompt += "Key points:\n"
            
            for chunk_result in page_result['results']:
                summary_prompt += f"- {chunk_result['result']}\n"
            
            summary_prompt += "\n"
        
        summary_prompt += (
            "Based on all this information, provide a comprehensive answer to the user's query. "
            "Include references to specific pages where the information was found."
        )
        
        messages = [
            {"role": "system", "content": "You are a helpful assistant that synthesizes information from multiple sources."},
            {"role": "user", "content": summary_prompt}
        ]
        
        try:
            response = litellm.completion(
                messages=messages,
                model="openai/gpt-3.5-turbo",
                api_key=os.environ.get("LLM_API_KEY", ""),
                base_url=os.environ.get("LLM_BASE_URL", ""),
                stream=False,
                max_tokens=1500,
                temperature=0.3,
            )
            
            final_answer = response.choices[0].message.content.strip()
            return final_answer
            
        except Exception as e:
            logger.error(f"Error creating summary: {str(e)}")
            # Fall back to returning individual page results
            final_answer = f"Error creating summary: {str(e)}\n\nHere are the individual page results:\n\n"
            
            for page_result in all_results:
                final_answer += f"## {page_result['page_title']}\n"
                final_answer += f"URL: {page_result['page_url']}\n\n"
                
                for chunk_result in page_result['results']:
                    final_answer += f"### Chunk {chunk_result['chunk']}:\n{chunk_result['result']}\n\n"
            
            return final_answer
    
    # If we only have one page with results
    elif len(all_results) == 1:
        page_result = all_results[0]
        
        if len(page_result['results']) == 1:
            # If there's only one chunk result, return it directly
            return f"# {page_result['page_title']}\n\n{page_result['results'][0]['result']}\n\nSource: {page_result['page_url']}"
        else:
            # If there are multiple chunks, summarize them
            summary_prompt = (
                f"You've analyzed the Confluence page '{page_result['page_title']}' to answer this query: '{user_query}'\n\n"
                "Here are the key findings from different sections of the page:\n\n"
            )
            
            for chunk_result in page_result['results']:
                summary_prompt += f"Section {chunk_result['chunk']}:\n{chunk_result['result']}\n\n"
            
            summary_prompt += (
                "Based on all this information, provide a comprehensive answer to the user's query."
            )
            
            messages = [
                {"role": "system", "content": "You are a helpful assistant that synthesizes information from multiple sections of a document."},
                {"role": "user", "content": summary_prompt}
            ]
            
            try:
                response = litellm.completion(
                    messages=messages,
                    model="openai/gpt-3.5-turbo",
                    api_key=os.environ.get("LLM_API_KEY", ""),
                    base_url=os.environ.get("LLM_BASE_URL", ""),
                    stream=False,
                    max_tokens=1000,
                    temperature=0.3,
                )
                
                final_answer = response.choices[0].message.content.strip()
                return f"# {page_result['page_title']}\n\n{final_answer}\n\nSource: {page_result['page_url']}"
                
            except Exception as e:
                logger.error(f"Error creating page summary: {str(e)}")
                # Fall back to returning individual chunk results
                final_answer = f"# {page_result['page_title']}\n\nError creating summary: {str(e)}\n\nHere are the individual section results:\n\n"
                
                for chunk_result in page_result['results']:
                    final_answer += f"## Section {chunk_result['chunk']}:\n{chunk_result['result']}\n\n"
                
                final_answer += f"\nSource: {page_result['page_url']}"
                return final_answer
    
    return "No relevant information found in the space content."

# Chunk content into manageable pieces
def chunk_content(content: str, max_size: int = 8000) -> List[str]:
    """Split content into manageable chunks for LLM processing.
    
    Args:
        content: The text content to chunk
        max_size: Maximum size of each chunk in characters
        
    Returns:
        List[str]: List of content chunks
    """
    if len(content) <= max_size:
        return [content]
    
    # Try to split at paragraph boundaries
    paragraphs = content.split('\n\n')
    chunks = []
    current_chunk = ""
    
    for para in paragraphs:
        if len(current_chunk) + len(para) + 2 <= max_size:
            if current_chunk:
                current_chunk += '\n\n'
            current_chunk += para
        else:
            if current_chunk:
                chunks.append(current_chunk)
            
            # If a single paragraph is too large, split it further
            if len(para) > max_size:
                # Split at sentence boundaries
                sentences = para.replace('. ', '.\n').split('\n')
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

def execute_confluence_action(action: str, **kwargs) -> Dict[str, Any]:
    """Execute a Confluence action with the given parameters.
    
    Args:
        action: The action to execute
        **kwargs: Additional parameters for the action
        
    Returns:
        Dict[str, Any]: Result of the action
    """
    logger.info(f"Executing Confluence {action} action with params: {kwargs}")
    
    # Validate connection
    valid, message = validate_confluence_connection()
    if not valid:
        return {"success": False, "error": message}
    
    space_key = kwargs.get('space_key')
    limit = kwargs.get('limit')
    query = kwargs.get('query', '')
    
    if not space_key:
        return {"success": False, "error": "Space key is required"}
    
    # Get space content
    logger.info(f"Retrieving content from space: {space_key}")
    content_result = get_space_content(space_key, limit)
    
    if not content_result:
        return {"success": False, "error": f"Failed to retrieve content from space: {space_key}"}
    
    # Check if we got any results
    page_count = content_result.get("page", {}).get("size", 0)
    blog_count = content_result.get("blogpost", {}).get("size", 0)
    
    if page_count == 0 and blog_count == 0:
        return {"success": True, "message": f"No content found in space: {space_key}"}
    
    # If no query, just return the content list
    if not query:
        result = {"success": True, "space_key": space_key}
        
        # Format pages
        if page_count > 0:
            pages = []
            for page in content_result.get("page", {}).get("results", []):
                pages.append({
                    "id": page.get("id"),
                    "title": page.get("title"),
                    "type": page.get("type"),
                    "url": f"{os.environ.get('CONFLUENCE_URL', '').rstrip('/')}/display/{space_key}/{page.get('id')}"
                })
            result["pages"] = pages
            result["page_count"] = page_count
        
        # Format blog posts
        if blog_count > 0:
            blogs = []
            for blog in content_result.get("blogpost", {}).get("results", []):
                blogs.append({
                    "id": blog.get("id"),
                    "title": blog.get("title"),
                    "type": blog.get("type"),
                    "url": f"{os.environ.get('CONFLUENCE_URL', '').rstrip('/')}/display/{space_key}/{blog.get('id')}"
                })
            result["blogs"] = blogs
            result["blog_count"] = blog_count
        
        return result
    else:
        # Process with query
        logger.info(f"Processing query: {query}")
        
        # Get full content of each page
        pages = []
        
        # Extract page IDs and titles
        if "page" in content_result and "results" in content_result["page"]:
            for page in content_result["page"]["results"]:
                page_id = page.get("id")
                if page_id:
                    page_content = get_page_content(page_id)
                    if page_content:
                        pages.append(page_content)
        
        # Process with LLM
        if not pages:
            return {"success": True, "message": "No page content found to process"}
        
        result = process_with_llm(pages, query)
        return {"success": True, "answer": result}

if __name__ == "__main__":
    # Check for required environment variables
    if not os.environ.get("CONFLUENCE_URL") or not os.environ.get("CONFLUENCE_USERNAME") or not os.environ.get("CONFLUENCE_API_TOKEN"):
        logger.error("Confluence credentials not properly configured")
        print(json.dumps({"success": False, "error": "Confluence credentials not properly configured"}))
        sys.exit(1)

    logger.info("Starting Confluence space content execution...")
    
    # Get arguments from environment variables
    args = {}
    for arg in ["space_key", "limit", "query"]:
        if arg in os.environ:
            args[arg] = os.environ[arg]
    
    result = execute_confluence_action("confluence_space_content", **args)
    logger.info("Confluence space content execution completed")
    print(json.dumps(result)) 