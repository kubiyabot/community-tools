import logging
from typing import Dict, Any, List, Optional
import hubspot
from hubspot.crm.deals import ApiException

logger = logging.getLogger(__name__)

class DealsOperations:
    def __init__(self, access_token: str):
        self.client = hubspot.Client.create(access_token=access_token)
    
    def create_deal(self, deal_name: str, pipeline: str, stage: str, amount: Optional[float] = None, 
                   properties: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create a new deal in HubSpot."""
        try:
            deal_properties = {
                "dealname": deal_name,
                "pipeline": pipeline,
                "dealstage": stage
            }
            
            if amount is not None:
                deal_properties["amount"] = str(amount)
                
            if properties:
                deal_properties.update(properties)
                
            response = self.client.crm.deals.basic_api.create(
                simple_public_object_input={"properties": deal_properties}
            )
            return response.to_dict()
            
        except ApiException as e:
            logger.error(f"Failed to create deal: {str(e)}")
            raise
    
    def get_deal(self, deal_id: str) -> Dict[str, Any]:
        """Get deal details by ID."""
        try:
            response = self.client.crm.deals.basic_api.get_by_id(deal_id)
            return response.to_dict()
        except ApiException as e:
            logger.error(f"Failed to get deal: {str(e)}")
            raise
    
    def update_deal(self, deal_id: str, properties: Dict[str, Any]) -> Dict[str, Any]:
        """Update deal properties."""
        try:
            response = self.client.crm.deals.basic_api.update(
                deal_id,
                simple_public_object_input={"properties": properties}
            )
            return response.to_dict()
        except ApiException as e:
            logger.error(f"Failed to update deal: {str(e)}")
            raise
    
    def search_deals(self, query: str, properties: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Search for deals based on a query."""
        try:
            search_request = {
                "query": query,
                "properties": properties or ["dealname", "pipeline", "dealstage", "amount"]
            }
            
            response = self.client.crm.deals.search_api.do_search(
                public_object_search_request=search_request
            )
            return [result.to_dict() for result in response.results]
        except ApiException as e:
            logger.error(f"Failed to search deals: {str(e)}")
            raise
    
    def delete_deal(self, deal_id: str) -> None:
        """Delete a deal by ID."""
        try:
            self.client.crm.deals.basic_api.archive(deal_id)
        except ApiException as e:
            logger.error(f"Failed to delete deal: {str(e)}")
            raise
            
    def associate_with_company(self, deal_id: str, company_id: str) -> Dict[str, Any]:
        """Associate a deal with a company."""
        try:
            response = self.client.crm.deals.associations_api.create(
                deal_id,
                "companies",
                company_id,
                [{"association_type": "deal_to_company"}]
            )
            return response.to_dict()
        except ApiException as e:
            logger.error(f"Failed to associate deal with company: {str(e)}")
            raise
            
    def associate_with_contact(self, deal_id: str, contact_id: str) -> Dict[str, Any]:
        """Associate a deal with a contact."""
        try:
            response = self.client.crm.deals.associations_api.create(
                deal_id,
                "contacts",
                contact_id,
                [{"association_type": "deal_to_contact"}]
            )
            return response.to_dict()
        except ApiException as e:
            logger.error(f"Failed to associate deal with contact: {str(e)}")
            raise 