from kubiya_sdk.tools import Arg
from kubiya_sdk.tools.registry import tool_registry
from typing import Dict, Any, List, Optional
from .base import HubSpotBaseTool

# Create companies tools
create_company = HubSpotBaseTool(
    name="hubspot_create_company",
    description="Create a new company in HubSpot",
    content="python /opt/scripts/hubspot_runner.py",
    args=[
        Arg(name="name", type="str", description="Company name", required=True),
        Arg(name="properties", type="dict", description="Additional company properties", required=False)
    ]
)

get_company = HubSpotBaseTool(
    name="hubspot_get_company",
    description="Get company details by ID",
    content="python /opt/scripts/hubspot_runner.py",
    args=[
        Arg(name="company_id", type="str", description="Company's ID", required=True)
    ]
)

update_company = HubSpotBaseTool(
    name="hubspot_update_company",
    description="Update company properties",
    content="python /opt/scripts/hubspot_runner.py",
    args=[
        Arg(name="company_id", type="str", description="Company's ID", required=True),
        Arg(name="properties", type="dict", description="Properties to update", required=True)
    ]
)

search_companies = HubSpotBaseTool(
    name="hubspot_search_companies",
    description="Search for companies",
    content="python /opt/scripts/hubspot_runner.py",
    args=[
        Arg(name="query", type="str", description="Search query", required=True),
        Arg(name="properties", type="list", description="Properties to include in results", required=False)
    ]
)

delete_company = HubSpotBaseTool(
    name="hubspot_delete_company",
    description="Delete a company",
    content="python /opt/scripts/hubspot_runner.py",
    args=[
        Arg(name="company_id", type="str", description="Company's ID", required=True)
    ]
)

get_company_contacts = HubSpotBaseTool(
    name="hubspot_get_company_contacts",
    description="Get all contacts associated with a company",
    content="python /opt/scripts/hubspot_runner.py",
    args=[
        Arg(name="company_id", type="str", description="Company's ID", required=True)
    ]
)

# Register tools
tool_registry.register("hubspot", create_company)
tool_registry.register("hubspot", get_company)
tool_registry.register("hubspot", update_company)
tool_registry.register("hubspot", search_companies)
tool_registry.register("hubspot", delete_company)
tool_registry.register("hubspot", get_company_contacts) 