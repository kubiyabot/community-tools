from kubiya_sdk.tools import Arg
from kubiya_sdk.tools.registry import tool_registry
from typing import Dict, Any, List, Optional
from .base import HubSpotBaseTool

# Create deals tools
create_deal = HubSpotBaseTool(
    name="hubspot_create_deal",
    description="Create a new deal in HubSpot",
    content="python /opt/scripts/hubspot_runner.py",
    args=[
        Arg(name="deal_name", type="str", description="Deal name", required=True),
        Arg(name="pipeline", type="str", description="Pipeline ID", required=True),
        Arg(name="stage", type="str", description="Stage ID", required=True),
        Arg(name="amount", type="float", description="Deal amount", required=False),
        Arg(name="properties", type="dict", description="Additional deal properties", required=False)
    ]
)

get_deal = HubSpotBaseTool(
    name="hubspot_get_deal",
    description="Get deal details by ID",
    content="python /opt/scripts/hubspot_runner.py",
    args=[
        Arg(name="deal_id", type="str", description="Deal's ID", required=True)
    ]
)

update_deal = HubSpotBaseTool(
    name="hubspot_update_deal",
    description="Update deal properties",
    content="python /opt/scripts/hubspot_runner.py",
    args=[
        Arg(name="deal_id", type="str", description="Deal's ID", required=True),
        Arg(name="properties", type="dict", description="Properties to update", required=True)
    ]
)

search_deals = HubSpotBaseTool(
    name="hubspot_search_deals",
    description="Search for deals",
    content="python /opt/scripts/hubspot_runner.py",
    args=[
        Arg(name="query", type="str", description="Search query", required=True),
        Arg(name="properties", type="list", description="Properties to include in results", required=False)
    ]
)

delete_deal = HubSpotBaseTool(
    name="hubspot_delete_deal",
    description="Delete a deal",
    content="python /opt/scripts/hubspot_runner.py",
    args=[
        Arg(name="deal_id", type="str", description="Deal's ID", required=True)
    ]
)

associate_deal_company = HubSpotBaseTool(
    name="hubspot_associate_deal_company",
    description="Associate a deal with a company",
    content="python /opt/scripts/hubspot_runner.py",
    args=[
        Arg(name="deal_id", type="str", description="Deal's ID", required=True),
        Arg(name="company_id", type="str", description="Company's ID", required=True)
    ]
)

associate_deal_contact = HubSpotBaseTool(
    name="hubspot_associate_deal_contact",
    description="Associate a deal with a contact",
    content="python /opt/scripts/hubspot_runner.py",
    args=[
        Arg(name="deal_id", type="str", description="Deal's ID", required=True),
        Arg(name="contact_id", type="str", description="Contact's ID", required=True)
    ]
)

# Register tools
tool_registry.register("hubspot", create_deal)
tool_registry.register("hubspot", get_deal)
tool_registry.register("hubspot", update_deal)
tool_registry.register("hubspot", search_deals)
tool_registry.register("hubspot", delete_deal)
tool_registry.register("hubspot", associate_deal_company)
tool_registry.register("hubspot", associate_deal_contact) 