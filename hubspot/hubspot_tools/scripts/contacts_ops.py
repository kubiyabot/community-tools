import logging
from typing import Dict, Any, List, Optional
import hubspot
from hubspot.crm.contacts import ApiException

logger = logging.getLogger(__name__)

class ContactsOperations:
    def __init__(self, access_token: str):
        self.client = hubspot.Client.create(access_token=access_token)
    
    def create_contact(self, email: str, firstname: str, lastname: str, properties: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create a new contact in HubSpot."""
        try:
            contact_properties = {
                "email": email,
                "firstname": firstname,
                "lastname": lastname
            }
            if properties:
                contact_properties.update(properties)
                
            response = self.client.crm.contacts.basic_api.create(
                simple_public_object_input={"properties": contact_properties}
            )
            return response.to_dict()
            
        except ApiException as e:
            logger.error(f"Failed to create contact: {str(e)}")
            raise
    
    def get_contact(self, contact_id: str) -> Dict[str, Any]:
        """Get contact details by ID."""
        try:
            response = self.client.crm.contacts.basic_api.get_by_id(contact_id)
            return response.to_dict()
        except ApiException as e:
            logger.error(f"Failed to get contact: {str(e)}")
            raise
    
    def update_contact(self, contact_id: str, properties: Dict[str, Any]) -> Dict[str, Any]:
        """Update contact properties."""
        try:
            response = self.client.crm.contacts.basic_api.update(
                contact_id,
                simple_public_object_input={"properties": properties}
            )
            return response.to_dict()
        except ApiException as e:
            logger.error(f"Failed to update contact: {str(e)}")
            raise
    
    def search_contacts(self, query: str, properties: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Search for contacts based on a query."""
        try:
            search_request = {
                "query": query,
                "properties": properties or ["email", "firstname", "lastname"]
            }
            
            response = self.client.crm.contacts.search_api.do_search(
                public_object_search_request=search_request
            )
            return [result.to_dict() for result in response.results]
        except ApiException as e:
            logger.error(f"Failed to search contacts: {str(e)}")
            raise
    
    def delete_contact(self, contact_id: str) -> None:
        """Delete a contact by ID."""
        try:
            self.client.crm.contacts.basic_api.archive(contact_id)
        except ApiException as e:
            logger.error(f"Failed to delete contact: {str(e)}")
            raise 