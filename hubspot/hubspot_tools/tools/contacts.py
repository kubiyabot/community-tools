from kubiya_sdk.tools import Arg
from kubiya_sdk.tools.registry import tool_registry
from typing import Dict, Any, List, Optional
from .base import HubSpotBaseTool

# Create contacts tools
create_contact = HubSpotBaseTool(
    name="hubspot_create_contact",
    description="Create a new contact in HubSpot",
    content="python /opt/scripts/hubspot_runner.py",
    args=[
        Arg(name="email", type="str", description="Contact's email address", required=True),
        Arg(name="firstname", type="str", description="Contact's first name", required=True),
        Arg(name="lastname", type="str", description="Contact's last name", required=True),
        Arg(name="properties", type="dict", description="Additional contact properties", required=False)
    ]
)

get_contact = HubSpotBaseTool(
    name="hubspot_get_contact",
    description="Get contact details by ID",
    content="python /opt/scripts/hubspot_runner.py",
    args=[
        Arg(name="contact_id", type="str", description="Contact's ID", required=True)
    ]
)

update_contact = HubSpotBaseTool(
    name="hubspot_update_contact",
    description="Update contact properties",
    content="python /opt/scripts/hubspot_runner.py",
    args=[
        Arg(name="contact_id", type="str", description="Contact's ID", required=True),
        Arg(name="properties", type="dict", description="Properties to update", required=True)
    ]
)

search_contacts = HubSpotBaseTool(
    name="hubspot_search_contacts",
    description="Search for contacts",
    content="python /opt/scripts/hubspot_runner.py",
    args=[
        Arg(name="query", type="str", description="Search query", required=True),
        Arg(name="properties", type="list", description="Properties to include in results", required=False)
    ]
)

delete_contact = HubSpotBaseTool(
    name="hubspot_delete_contact",
    description="Delete a contact",
    content="python /opt/scripts/hubspot_runner.py",
    args=[
        Arg(name="contact_id", type="str", description="Contact's ID", required=True)
    ]
)

# Register tools
tool_registry.register("hubspot", create_contact)
tool_registry.register("hubspot", get_contact)
tool_registry.register("hubspot", update_contact)
tool_registry.register("hubspot", search_contacts)
tool_registry.register("hubspot", delete_contact) 