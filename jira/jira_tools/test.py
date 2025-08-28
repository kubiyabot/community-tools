import os
import sys
import inspect
from base import JiraTool, Arg
from kubiya_sdk.tools.registry import tool_registry
from kubiya_sdk.tools import FileSpec

# Import the full script
from . import my_tickets_script


class MyTicketsTool:
    """Jira My Tickets tool using Python requests."""

    def __init__(self):
        """Initialize and register the My Tickets tool."""
        try:
            tool = self.my_tickets()
            tool_registry.register("jira", tool)
            print(f"✅ Registered: {tool.name}")
        except Exception as e:
            print(f"❌ Failed to register My Tickets tool: {str(e)}", file=sys.stderr)
            raise

    def my_tickets(self) -> JiraTool:
        """Get tickets assigned to the current user."""
        
        return JiraTool(
            name="my_tickets",
            description="Get tickets assigned to the current user from Jira. Returns tickets that are not in 'Done' status by default. Supports filtering by status.",
            content="""
pip install requests > /dev/null 2>&1

python /tmp/my_tickets_script.py --status_filter "$status_filter" --max_results "$max_results"
""",
            with_files=[
                FileSpec(
                    destination="/tmp/my_tickets_script.py",
                    content=inspect.getsource(my_tickets_script),
                ),
            ],
            args=[
                Arg(
                    name="status_filter", 
                    description="Filter by status. Use 'open' for non-closed tickets, 'closed' for closed tickets, or specify exact status name like 'In Progress'",
                    required=False
                ),
                Arg(
                    name="max_results", 
                    description="Maximum number of results to return (default: 500). The tool will automatically handle pagination to fetch all results up to this limit.",
                    required=False
                )
            ],
            image="python:3.9-alpine"
        )


# Register the tool when the module is imported
if __name__ == "__main__":
    MyTicketsTool() 
