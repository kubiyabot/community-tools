import logging
from typing import Dict, Any, List, Optional
import hubspot
from hubspot.crm.companies import ApiException

logger = logging.getLogger(__name__)

class CompaniesOperations:
    def __init__(self, access_token: str):
        self.client = hubspot.Client.create(access_token=access_token)
    
    def create_company(self, name: str, properties: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create a new company in HubSpot."""
        try:
            company_properties = {
                "name": name
            }
            if properties:
                company_properties.update(properties)
                
            response = self.client.crm.companies.basic_api.create(
                simple_public_object_input={"properties": company_properties}
            )
            return response.to_dict()
            
        except ApiException as e:
            logger.error(f"Failed to create company: {str(e)}")
            raise
    
    def get_company(self, company_id: str) -> Dict[str, Any]:
        """Get company details by ID."""
        try:
            response = self.client.crm.companies.basic_api.get_by_id(company_id)
            return response.to_dict()
        except ApiException as e:
            logger.error(f"Failed to get company: {str(e)}")
            raise
    
    def update_company(self, company_id: str, properties: Dict[str, Any]) -> Dict[str, Any]:
        """Update company properties."""
        try:
            response = self.client.crm.companies.basic_api.update(
                company_id,
                simple_public_object_input={"properties": properties}
            )
            return response.to_dict()
        except ApiException as e:
            logger.error(f"Failed to update company: {str(e)}")
            raise
    
    def search_companies(self, query: str, properties: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Search for companies based on a query."""
        try:
            search_request = {
                "query": query,
                "properties": properties or ["name", "domain", "industry"]
            }
            
            response = self.client.crm.companies.search_api.do_search(
                public_object_search_request=search_request
            )
            return [result.to_dict() for result in response.results]
        except ApiException as e:
            logger.error(f"Failed to search companies: {str(e)}")
            raise
    
    def delete_company(self, company_id: str) -> None:
        """Delete a company by ID."""
        try:
            self.client.crm.companies.basic_api.archive(company_id)
        except ApiException as e:
            logger.error(f"Failed to delete company: {str(e)}")
            raise
            
    def get_contacts(self, company_id: str) -> List[Dict[str, Any]]:
        """Get all contacts associated with a company."""
        try:
            response = self.client.crm.companies.associations_api.get_all(
                company_id,
                "contacts"
            )
            return [result.to_dict() for result in response.results]
        except ApiException as e:
            logger.error(f"Failed to get company contacts: {str(e)}")
            raise 