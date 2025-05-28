from typing import List
import sys
from .base import PostgresCliTool
from kubiya_sdk.tools import Arg
from kubiya_sdk.tools.registry import tool_registry

class PostgresOperations:
    """PostgreSQL database operations and management tools."""

    def __init__(self):
        """Initialize and register all PostgreSQL operation tools."""
        try:
            tools = [
                self.query_users_table(),
                self.run_custom_readonly_query(),
                self.check_postgres_connection(),
                self.get_connection_string(),
                self.list_tables()
            ]
            
            for tool in tools:
                try:
                    tool_registry.register("postgres", tool)
                    print(f"✅ Registered: {tool.name}")
                except Exception as e:
                    print(f"❌ Failed to register {tool.name}: {str(e)}", file=sys.stderr)
                    raise
        except Exception as e:
            print(f"❌ Failed to register PostgreSQL operation tools: {str(e)}", file=sys.stderr)
            raise

    def query_users_table(self) -> PostgresCliTool:
        """Runs SELECT * FROM users against the prod Postgres DB in Kubernetes."""
        return PostgresCliTool(
            name="query_users_table",
            description="Runs SELECT * FROM users against the prod Postgres DB in Kubernetes.",
            content='psql -c "SELECT * FROM users;"',
            args=[]
        )

    def run_custom_readonly_query(self) -> PostgresCliTool:
        """Runs a safe SELECT query against the production Postgres database."""
        return PostgresCliTool(
            name="run_custom_readonly_query",
            description="Runs a safe SELECT query against the production Postgres database.",
            content="""
validate_postgres_connection

if echo "$query" | grep -Ei 'drop|delete|update|insert|alter|create'; then
  echo "❌ Unsafe query detected. Only SELECT statements are allowed."
  exit 1
fi

psql -c "$query"
""",
            args=[
                Arg(name="query", type="str", description="SQL SELECT query to execute", required=True)
            ]
        )

    def check_postgres_connection(self) -> PostgresCliTool:
        """Checks the connectivity to the production PostgreSQL database."""
        return PostgresCliTool(
            name="check_postgres_connection",
            description="Checks the connectivity to the production PostgreSQL database.",
            content="""
validate_postgres_connection
echo "✅ Successfully connected to PostgreSQL"
""",
            args=[]
        )

    def get_connection_string(self) -> PostgresCliTool:
        """Returns the PostgreSQL connection string (password redacted)."""
        return PostgresCliTool(
            name="get_connection_string",
            description="Returns the PostgreSQL connection string (password redacted).",
            content="""
echo "postgres://$PGUSER:*****@$PGHOST:$PGPORT/$PGDATABASE"
""",
            args=[]
        )

    def list_tables(self) -> PostgresCliTool:
        """Lists all tables in the connected Postgres DB."""
        return PostgresCliTool(
            name="list_postgres_tables",
            description="Lists all tables in the connected Postgres DB.",
            content='psql -c "\\dt"',
            args=[]
        )

# Initialize tools
PostgresOperations()