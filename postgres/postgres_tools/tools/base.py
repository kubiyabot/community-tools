from typing import List, Optional, Dict, Any
from kubiya_sdk.tools import Tool, Arg

POSTGRES_ICON_URL = "https://cdn-icons-png.flaticon.com/512/5968/5968342.png"

class PostgresCliTool(Tool):
    """Base class for all PostgreSQL tools."""
    
    name: str
    description: str
    content: str = ""
    args: List[Arg] = []
    image: str = "bitnami/postgresql:latest"
    icon_url: str = POSTGRES_ICON_URL
    type: str = "docker"
    
    def __init__(self, name, description, content, args=None, image="bitnami/postgresql:latest"):
        # Add helper functions to the content
        helper_functions = """
            # Helper functions for PostgreSQL tools
            validate_postgres_connection() {
                if [ -z "$PGUSER" ]; then
                    echo "Error: PGUSER environment variable is not set"
                    exit 1
                fi

                if [ -z "$PGPASSWORD" ]; then
                    echo "Error: PGPASSWORD environment variable is not set"
                    exit 1
                fi

                if [ -z "$PGDATABASE" ]; then
                    echo "Error: PGDATABASE environment variable is not set"
                    exit 1
                fi

                if [ -z "$PGHOST" ]; then
                    echo "Error: PGHOST environment variable is not set"
                    exit 1
                fi

                if [ -z "$PGPORT" ]; then
                    echo "Error: PGPORT environment variable is not set"
                    exit 1
                fi

                # Test connection
                if ! pg_isready -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d "$PGDATABASE" > /dev/null 2>&1; then
                    echo "Error: Could not connect to PostgreSQL database"
                    exit 1
                fi
            }
        """
        
        content = helper_functions + "\n" + content
        
        super().__init__(
            name=name,
            description=description,
            content=content,
            args=args or [],
            image=image,
            icon_url=POSTGRES_ICON_URL,
            type="docker",
            secrets=["PGPASSWORD"],
            env=["PGUSER", "PGDATABASE", "PGHOST", "PGPORT"]
        )

    def get_args(self) -> List[Arg]:
        """Return the tool's arguments."""
        return self.args

    def get_content(self) -> str:
        """Return the tool's shell script content."""
        return self.content

    def get_image(self) -> str:
        """Return the Docker image to use."""
        return self.image

    def validate_args(self, args: Dict[str, Any]) -> bool:
        """Validate the provided arguments."""
        required_args = [arg.name for arg in self.args if arg.required]
        return all(arg in args and args[arg] for arg in required_args)

    def get_error_message(self, args: Dict[str, Any]) -> Optional[str]:
        """Return error message if arguments are invalid."""
        missing_args = []
        for arg in self.args:
            if arg.required and (arg.name not in args or not args[arg.name]):
                missing_args.append(arg.name)
        
        if missing_args:
            return f"Missing required arguments: {', '.join(missing_args)}"
        return None
