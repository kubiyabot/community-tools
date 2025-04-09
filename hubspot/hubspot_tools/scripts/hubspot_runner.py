import os
import sys
import json
import logging
from typing import Dict, Any, List, Optional
import hubspot
from hubspot.crm import contacts, companies, deals
from hubspot.crm.associations import ApiException

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class HubSpotError(Exception):
    """Custom exception for HubSpot operations."""
    pass

def get_api_client(entity_type: str, client: hubspot.Client):
    """Get the appropriate API client based on entity type."""
    try:
        if entity_type == 'contacts':
            return client.crm.contacts
        elif entity_type == 'companies':
            return client.crm.companies
        elif entity_type == 'deals':
            return client.crm.deals
        else:
            raise HubSpotError(f"❌ Unsupported entity type: {entity_type}")
    except Exception as e:
        raise HubSpotError(f"❌ Failed to get API client: {str(e)}")

def paginate_results(api, search_request: Dict[str, Any], page_size: int, max_results: int) -> List[Dict[str, Any]]:
    """Paginate through search results with limits."""
    results = []
    after = None
    total_processed = 0
    
    logger.info(f"📄 Fetching results (page size: {page_size}, max results: {max_results})")
    
    while total_processed < max_results:
        try:
            # Add pagination parameters
            search_request['limit'] = min(page_size, max_results - total_processed)
            if after:
                search_request['after'] = after
            
            # Execute search
            response = api.search_api.do_search(
                public_object_search_request=search_request
            )
            
            # Process results
            batch = [r.to_dict() for r in response.results]
            results.extend(batch)
            total_processed += len(batch)
            
            # Check if we have more results
            if not response.paging or not response.paging.next:
                break
                
            after = response.paging.next.after
            logger.info(f"✓ Fetched {len(batch)} results (total: {total_processed})")
            
        except Exception as e:
            raise HubSpotError(f"❌ Failed to fetch page: {str(e)}")
    
    logger.info(f"✅ Completed fetching {total_processed} results")
    return results

def execute_operation():
    """Execute the requested HubSpot operation."""
    try:
        # Load configuration
        with open('/tmp/hubspot_config.json', 'r') as f:
            config = json.load(f)
            
        # Get operation parameters
        entity_type = config['entity_type']
        operation = config['operation']
        params = config['parameters']
        page_size = config.get('page_size', 100)
        max_results = config.get('max_results', 1000)
        
        logger.info(f"🔄 Executing {operation} operation on {entity_type}")
        
        # Initialize client
        client = hubspot.Client.create(access_token=os.environ['HUBSPOT_ACCESS_TOKEN'])
        api = get_api_client(entity_type, client)
        
        try:
            # Execute operation
            if operation == 'create':
                logger.info(f"📝 Creating new {entity_type} entry")
                response = api.basic_api.create(
                    simple_public_object_input={"properties": params}
                )
                logger.info("✅ Successfully created entry")
                
            elif operation == 'get':
                logger.info(f"🔍 Fetching {entity_type} with ID: {params['id']}")
                response = api.basic_api.get_by_id(params['id'])
                logger.info("✅ Successfully retrieved entry")
                
            elif operation == 'update':
                logger.info(f"📝 Updating {entity_type} with ID: {params['id']}")
                response = api.basic_api.update(
                    params['id'],
                    simple_public_object_input={"properties": params['properties']}
                )
                logger.info("✅ Successfully updated entry")
                
            elif operation == 'delete':
                logger.info(f"🗑️ Deleting {entity_type} with ID: {params['id']}")
                api.basic_api.archive(params['id'])
                logger.info("✅ Successfully deleted entry")
                return None
                
            elif operation == 'search':
                logger.info(f"🔍 Searching {entity_type}")
                search_request = {
                    "query": params['query'],
                    "properties": params.get('properties', [])
                }
                return paginate_results(api, search_request, page_size, max_results)
                
            elif operation == 'associate':
                logger.info(f"🔗 Creating association for {entity_type}")
                response = api.associations_api.create(
                    params['from_id'],
                    params['to_object_type'],
                    params['to_id'],
                    [{"association_type": params['association_type']}]
                )
                logger.info("✅ Successfully created association")
                
            else:
                raise HubSpotError(f"❌ Unsupported operation: {operation}")
            
            # Return result
            if hasattr(response, 'to_dict'):
                result = response.to_dict()
                logger.info(f"✅ Operation completed successfully")
                return result
            return response
            
        except ApiException as e:
            error_msg = f"❌ HubSpot API error: {str(e)}"
            if hasattr(e, 'status') and e.status == 429:
                error_msg = "❌ Rate limit exceeded. Please try again later."
            logger.error(error_msg)
            raise HubSpotError(error_msg)
            
        except Exception as e:
            error_msg = f"❌ Operation failed: {str(e)}"
            logger.error(error_msg)
            raise HubSpotError(error_msg)
            
    except Exception as e:
        error_msg = f"❌ Failed to execute operation: {str(e)}"
        logger.error(error_msg)
        print(json.dumps({"error": str(e)}))
        sys.exit(1)

if __name__ == '__main__':
    try:
        result = execute_operation()
        if result is not None:
            print(json.dumps({"result": result}))
    except Exception as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(1) 