"""HubSpot tools for Kubiya."""

from kubiya_sdk.tools.registry import register_tool
from .contacts_tool import ContactsTool
from .companies_tool import CompaniesTool
from .deals_tool import DealsTool
from .hubspot_tool import HubspotTool

# Register tools
register_tool("hubspot", HubspotTool)
register_tool("hubspot_contacts", ContactsTool)
register_tool("hubspot_companies", CompaniesTool)
register_tool("hubspot_deals", DealsTool)

__all__ = ['ContactsTool', 'CompaniesTool', 'DealsTool', 'HubspotTool']
