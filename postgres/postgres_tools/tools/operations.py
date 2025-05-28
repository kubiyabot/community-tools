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
                # Connection and Info Tools
                self.check_postgres_connection(),
                self.get_database_info(),
                
                # Schema and Table Management
                self.list_tables(),
                self.describe_table(),
                self.create_table(),
                self.drop_table(),
                self.list_schemas(),
                
                # Data Operations
                self.run_select_query(),
                self.insert_data(),
                self.update_data(),
                self.delete_data(),
                
                # User and Permission Management
                self.list_users(),
                self.check_user_permissions(),
                self.create_user(),
                self.grant_permissions(),
                
                # Backup and Maintenance
                self.backup_table(),
                self.analyze_table_stats(),
                self.check_table_sizes(),
                
                # Environment-specific Tools
                self.run_production_query()
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

    # Connection and Info Tools
    def check_postgres_connection(self) -> PostgresCliTool:
        """Checks the connectivity to the PostgreSQL database with troubleshooting info."""
        return PostgresCliTool(
            name="check_postgres_connection",
            description="Checks the connectivity to the PostgreSQL database with troubleshooting info.",
            content="""
echo "🔍 Testing PostgreSQL connection..."

if validate_postgres_connection; then
    echo "✅ Database connection successful"
    
    echo ""
    echo "📡 Connection Details:"
    echo "Host: $PGHOST"
    echo "Port: $PGPORT"
    echo "Database: $PGDATABASE"
    echo "User: $PGUSER"
    
    echo ""
    echo "⏱️ Testing query performance..."
    time psql -c "SELECT 1;" > /dev/null 2>&1
    
else
    echo "❌ Database connection failed"
    echo ""
    echo "🔧 Troubleshooting steps:"
    echo "1. Check VPN connection (Azure VPN or Checkpoint VPN)"
    echo "2. Verify IP whitelist for database access"
    echo "3. Check database credentials"
    echo "4. Ensure database server is running"
    
    echo ""
    echo "🌐 Testing network connectivity..."
    if command -v nc >/dev/null 2>&1; then
        if nc -z "$PGHOST" "$PGPORT" 2>/dev/null; then
            echo "✅ Network connectivity to $PGHOST:$PGPORT is working"
        else
            echo "❌ Cannot reach $PGHOST:$PGPORT - check VPN connection"
        fi
    fi
    
    exit 1
fi
""",
            args=[]
        )

    def get_database_info(self) -> PostgresCliTool:
        """Gets comprehensive database information including size, version, and settings."""
        return PostgresCliTool(
            name="get_postgres_database_info",
            description="Gets comprehensive database information including size, version, and settings.",
            content="""
echo "📊 PostgreSQL Database Information"
echo "=================================="

echo ""
echo "🔧 Version Information:"
psql -c "SELECT version();"

echo ""
echo "📈 Database Size:"
psql -c "
SELECT 
    pg_database.datname as database_name,
    pg_size_pretty(pg_database_size(pg_database.datname)) as size
FROM pg_database
WHERE datname = current_database();
"

echo ""
echo "📋 Connection Information:"
psql -c "
SELECT 
    current_database() as database,
    current_user as user,
    inet_server_addr() as server_ip,
    inet_server_port() as server_port;
"

echo ""
echo "⚙️ Database Settings:"
psql -c "
SELECT name, setting, unit, context 
FROM pg_settings 
WHERE name IN ('max_connections', 'shared_buffers', 'work_mem', 'maintenance_work_mem')
ORDER BY name;
"
""",
            args=[]
        )

    # Schema and Table Management
    def list_tables(self) -> PostgresCliTool:
        """Lists all tables in the database with additional information."""
        return PostgresCliTool(
            name="list_postgres_tables",
            description="Lists all tables in the database with additional information.",
            content="""
echo "📋 Database Tables"
echo "=================="

psql -c "
SELECT 
    schemaname as schema,
    tablename as table_name,
    tableowner as owner,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables 
WHERE schemaname NOT IN ('information_schema', 'pg_catalog')
ORDER BY schemaname, tablename;
"
""",
            args=[]
        )

    def describe_table(self) -> PostgresCliTool:
        """Describes the structure of a specific table."""
        return PostgresCliTool(
            name="describe_postgres_table",
            description="Describes the structure of a specific table.",
            content="""
echo "📋 Table Structure: $table_name"
echo "==============================="

psql -c "\\d+ $table_name"

echo ""
echo "📊 Table Statistics:"
psql -c "
SELECT 
    schemaname,
    tablename,
    attname as column_name,
    n_distinct,
    correlation
FROM pg_stats 
WHERE tablename = '$table_name'
ORDER BY attname;
"
""",
            args=[
                Arg(name="table_name", type="str", description="Name of the table to describe", required=True)
            ]
        )

    def create_table(self) -> PostgresCliTool:
        """Creates a new table by specifying table name, columns, and constraints."""
        return PostgresCliTool(
            name="create_postgres_table",
            description="Creates a new table by specifying table name, columns, and constraints.",
            content="""
echo "🔨 Creating table: $table_name"
echo "Columns: $columns"
if [ -n "$primary_key" ]; then
    echo "Primary Key: $primary_key"
fi
if [ -n "$constraints" ]; then
    echo "Additional Constraints: $constraints"
fi
echo ""

# Build the CREATE TABLE statement
SQL="CREATE TABLE $table_name ("

# Add columns
SQL="$SQL$columns"

# Add primary key if specified
if [ -n "$primary_key" ]; then
    SQL="$SQL, PRIMARY KEY ($primary_key)"
fi

# Add additional constraints if specified
if [ -n "$constraints" ]; then
    SQL="$SQL, $constraints"
fi

SQL="$SQL);"

echo "Generated SQL:"
echo "$SQL"
echo ""

psql -c "$SQL"

if [ $? -eq 0 ]; then
    echo "✅ Table '$table_name' created successfully"
    
    # Show the created table structure
    echo ""
    echo "📋 Table Structure:"
    psql -c "\\d+ $table_name"
else
    echo "❌ Failed to create table"
    exit 1
fi
""",
            args=[
                Arg(name="table_name", type="str", description="Name of the table to create", required=True),
                Arg(name="columns", type="str", description="Column definitions (e.g., 'id SERIAL, name VARCHAR(100) NOT NULL, email VARCHAR(255) UNIQUE, created_at TIMESTAMP DEFAULT NOW()')", required=True),
                Arg(name="primary_key", type="str", description="Primary key column name (optional, e.g., 'id')", required=False),
                Arg(name="constraints", type="str", description="Additional constraints (optional, e.g., 'UNIQUE(email), CHECK(age > 0)')", required=False)
            ]
        )

    def drop_table(self) -> PostgresCliTool:
        """Drops a table from the database."""
        return PostgresCliTool(
            name="drop_postgres_table",
            description="Drops a table from the database.",
            content="""
echo "⚠️  WARNING: This will permanently delete the table '$table_name'"
echo "Table: $table_name"
echo ""

if [ "$confirm" != "yes" ]; then
    echo "❌ Operation cancelled. Set confirm=yes to proceed."
    exit 1
fi

echo "🗑️  Dropping table..."
psql -c "DROP TABLE IF EXISTS $table_name;"

if [ $? -eq 0 ]; then
    echo "✅ Table dropped successfully"
else
    echo "❌ Failed to drop table"
    exit 1
fi
""",
            args=[
                Arg(name="table_name", type="str", description="Name of the table to drop", required=True),
                Arg(name="confirm", type="str", description="Type 'yes' to confirm deletion", required=True)
            ]
        )

    def list_schemas(self) -> PostgresCliTool:
        """Lists all schemas in the database."""
        return PostgresCliTool(
            name="list_postgres_schemas",
            description="Lists all schemas in the database.",
            content="""
echo "📁 Database Schemas"
echo "==================="

psql -c "
SELECT 
    schema_name,
    schema_owner
FROM information_schema.schemata
WHERE schema_name NOT IN ('information_schema', 'pg_catalog', 'pg_toast')
ORDER BY schema_name;
"
""",
            args=[]
        )

    # Data Operations
    def run_select_query(self) -> PostgresCliTool:
        """Runs a SELECT query against the database."""
        return PostgresCliTool(
            name="run_postgres_select_query",
            description="Runs a SELECT query against the database.",
            content="""
# Validate it's a SELECT query
if ! echo "$query" | grep -Ei '^[[:space:]]*select'; then
    echo "❌ Only SELECT queries are allowed"
    exit 1
fi

# Check for unsafe operations
if echo "$query" | grep -Ei 'drop|delete|update|insert|alter|create|truncate'; then
    echo "❌ Unsafe operations detected in query"
    exit 1
fi

echo "🔍 Executing SELECT query..."
echo "Query: $query"
echo ""

psql -c "$query"
""",
            args=[
                Arg(name="query", type="str", description="SELECT query to execute", required=True)
            ]
        )

    def insert_data(self) -> PostgresCliTool:
        """Inserts data into a table."""
        return PostgresCliTool(
            name="insert_postgres_data",
            description="Inserts data into a table.",
            content="""
echo "➕ Inserting data into table..."
echo "SQL: $insert_sql"
echo ""

psql -c "$insert_sql"

if [ $? -eq 0 ]; then
    echo "✅ Data inserted successfully"
else
    echo "❌ Failed to insert data"
    exit 1
fi
""",
            args=[
                Arg(name="insert_sql", type="str", description="Complete INSERT SQL statement", required=True)
            ]
        )

    def update_data(self) -> PostgresCliTool:
        """Updates data in a table."""
        return PostgresCliTool(
            name="update_postgres_data",
            description="Updates data in a table.",
            content="""
echo "✏️  Updating data in table..."
echo "SQL: $update_sql"
echo ""

if [ "$confirm" != "yes" ]; then
    echo "❌ Operation cancelled. Set confirm=yes to proceed with UPDATE."
    exit 1
fi

psql -c "$update_sql"

if [ $? -eq 0 ]; then
    echo "✅ Data updated successfully"
else
    echo "❌ Failed to update data"
    exit 1
fi
""",
            args=[
                Arg(name="update_sql", type="str", description="Complete UPDATE SQL statement", required=True),
                Arg(name="confirm", type="str", description="Type 'yes' to confirm update", required=True)
            ]
        )

    def delete_data(self) -> PostgresCliTool:
        """Deletes data from a table."""
        return PostgresCliTool(
            name="delete_postgres_data",
            description="Deletes data from a table.",
            content="""
echo "🗑️  Deleting data from table..."
echo "SQL: $delete_sql"
echo ""

if [ "$confirm" != "yes" ]; then
    echo "❌ Operation cancelled. Set confirm=yes to proceed with DELETE."
    exit 1
fi

psql -c "$delete_sql"

if [ $? -eq 0 ]; then
    echo "✅ Data deleted successfully"
else
    echo "❌ Failed to delete data"
    exit 1
fi
""",
            args=[
                Arg(name="delete_sql", type="str", description="Complete DELETE SQL statement", required=True),
                Arg(name="confirm", type="str", description="Type 'yes' to confirm deletion", required=True)
            ]
        )

    # User and Permission Management
    def list_users(self) -> PostgresCliTool:
        """Lists all database users and their roles."""
        return PostgresCliTool(
            name="list_postgres_users",
            description="Lists all database users and their roles.",
            content="""
echo "👥 Database Users and Roles"
echo "==========================="

psql -c "
SELECT 
    rolname as username,
    rolsuper as is_superuser,
    rolcreaterole as can_create_roles,
    rolcreatedb as can_create_databases,
    rolcanlogin as can_login,
    rolconnlimit as connection_limit
FROM pg_roles
ORDER BY rolname;
"
""",
            args=[]
        )

    def check_user_permissions(self) -> PostgresCliTool:
        """Checks permissions for the current user or a specific user."""
        return PostgresCliTool(
            name="check_postgres_user_permissions",
            description="Checks permissions for the current user or a specific user.",
            content="""
USER_TO_CHECK=${username:-$PGUSER}

echo "🔍 Checking permissions for user: $USER_TO_CHECK"
echo "================================================"

echo ""
echo "📋 Table Permissions:"
psql -c "
SELECT 
    schemaname,
    tablename,
    has_table_privilege('$USER_TO_CHECK', schemaname||'.'||tablename, 'SELECT') as can_select,
    has_table_privilege('$USER_TO_CHECK', schemaname||'.'||tablename, 'INSERT') as can_insert,
    has_table_privilege('$USER_TO_CHECK', schemaname||'.'||tablename, 'UPDATE') as can_update,
    has_table_privilege('$USER_TO_CHECK', schemaname||'.'||tablename, 'DELETE') as can_delete
FROM pg_tables 
WHERE schemaname NOT IN ('information_schema', 'pg_catalog')
ORDER BY schemaname, tablename;
"

echo ""
echo "🔐 Role Memberships:"
psql -c "
SELECT 
    r.rolname as role,
    m.rolname as member
FROM pg_roles r
JOIN pg_auth_members am ON r.oid = am.roleid
JOIN pg_roles m ON am.member = m.oid
WHERE m.rolname = '$USER_TO_CHECK'
ORDER BY r.rolname;
"
""",
            args=[
                Arg(name="username", type="str", description="Username to check (optional, defaults to current user)", required=False)
            ]
        )

    def create_user(self) -> PostgresCliTool:
        """Creates a new database user."""
        return PostgresCliTool(
            name="create_postgres_user",
            description="Creates a new database user.",
            content="""
echo "👤 Creating new user: $username"
echo "=============================="

CREATE_USER_SQL="CREATE USER $username"

if [ -n "$password" ]; then
    CREATE_USER_SQL="$CREATE_USER_SQL WITH PASSWORD '$password'"
fi

if [ "$can_login" = "true" ]; then
    CREATE_USER_SQL="$CREATE_USER_SQL LOGIN"
fi

if [ "$can_create_db" = "true" ]; then
    CREATE_USER_SQL="$CREATE_USER_SQL CREATEDB"
fi

CREATE_USER_SQL="$CREATE_USER_SQL;"

echo "Executing: CREATE USER $username WITH [options]"
psql -c "$CREATE_USER_SQL"

if [ $? -eq 0 ]; then
    echo "✅ User created successfully"
else
    echo "❌ Failed to create user"
    exit 1
fi
""",
            args=[
                Arg(name="username", type="str", description="Username for the new user", required=True),
                Arg(name="password", type="str", description="Password for the new user", required=False),
                Arg(name="can_login", type="str", description="Whether user can login (true/false)", required=False),
                Arg(name="can_create_db", type="str", description="Whether user can create databases (true/false)", required=False)
            ]
        )

    def grant_permissions(self) -> PostgresCliTool:
        """Grants permissions to a user on a table or database."""
        return PostgresCliTool(
            name="grant_postgres_permissions",
            description="Grants permissions to a user on a table or database.",
            content="""
echo "🔐 Granting permissions..."
echo "User: $username"
echo "Permissions: $permissions"
echo "Object: $object_name"
echo ""

GRANT_SQL="GRANT $permissions ON $object_name TO $username;"

echo "Executing: $GRANT_SQL"
psql -c "$GRANT_SQL"

if [ $? -eq 0 ]; then
    echo "✅ Permissions granted successfully"
else
    echo "❌ Failed to grant permissions"
    exit 1
fi
""",
            args=[
                Arg(name="username", type="str", description="Username to grant permissions to", required=True),
                Arg(name="permissions", type="str", description="Permissions to grant (e.g., SELECT, INSERT, ALL)", required=True),
                Arg(name="object_name", type="str", description="Table or database name", required=True)
            ]
        )

    # Backup and Maintenance
    def backup_table(self) -> PostgresCliTool:
        """Creates a backup of a specific table."""
        return PostgresCliTool(
            name="backup_postgres_table",
            description="Creates a backup of a specific table.",
            content="""
BACKUP_FILE="${table_name}_backup_$(date +%Y%m%d_%H%M%S).sql"

echo "💾 Creating backup of table: $table_name"
echo "Backup file: $BACKUP_FILE"
echo ""

pg_dump -t "$table_name" --data-only --inserts > "$BACKUP_FILE"

if [ $? -eq 0 ]; then
    echo "✅ Table backup created successfully"
    echo "📁 Backup saved as: $BACKUP_FILE"
    ls -lh "$BACKUP_FILE"
else
    echo "❌ Failed to create backup"
    exit 1
fi
""",
            args=[
                Arg(name="table_name", type="str", description="Name of the table to backup", required=True)
            ]
        )

    def analyze_table_stats(self) -> PostgresCliTool:
        """Analyzes table statistics and performance information."""
        return PostgresCliTool(
            name="analyze_postgres_table_stats",
            description="Analyzes table statistics and performance information.",
            content="""
echo "📊 Analyzing table statistics: $table_name"
echo "=========================================="

echo ""
echo "📈 Row Count and Size:"
psql -c "
SELECT 
    schemaname,
    tablename,
    n_tup_ins as inserts,
    n_tup_upd as updates,
    n_tup_del as deletes,
    n_live_tup as live_rows,
    n_dead_tup as dead_rows,
    pg_size_pretty(pg_total_relation_size('$table_name')) as total_size
FROM pg_stat_user_tables 
WHERE tablename = '$table_name';
"

echo ""
echo "🔍 Column Statistics:"
psql -c "
SELECT 
    attname as column_name,
    n_distinct,
    most_common_vals[1:3] as top_values,
    correlation
FROM pg_stats 
WHERE tablename = '$table_name'
ORDER BY attname;
"

echo ""
echo "🚀 Index Usage:"
psql -c "
SELECT 
    indexrelname as index_name,
    idx_tup_read as index_reads,
    idx_tup_fetch as index_fetches
FROM pg_stat_user_indexes 
WHERE relname = '$table_name'
ORDER BY idx_tup_read DESC;
"
""",
            args=[
                Arg(name="table_name", type="str", description="Name of the table to analyze", required=True)
            ]
        )

    def check_table_sizes(self) -> PostgresCliTool:
        """Shows the size of all tables in the database."""
        return PostgresCliTool(
            name="check_postgres_table_sizes",
            description="Shows the size of all tables in the database.",
            content="""
echo "📊 Table Sizes"
echo "=============="

psql -c "
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as total_size,
    pg_size_pretty(pg_relation_size(schemaname||'.'||tablename)) as table_size,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename) - pg_relation_size(schemaname||'.'||tablename)) as index_size,
    pg_total_relation_size(schemaname||'.'||tablename) as size_bytes
FROM pg_tables 
WHERE schemaname NOT IN ('information_schema', 'pg_catalog')
ORDER BY size_bytes DESC;
"
""",
            args=[]
        )

    def run_production_query(self) -> PostgresCliTool:
        """Runs a SELECT query on production database with enhanced safety and logging."""
        return PostgresCliTool(
            name="run_postgres_production_query",
            description="Runs a SELECT query on production database with enhanced safety and logging.",
            content="""
# Validate it's a SELECT query
if ! echo "$query" | grep -Ei '^[[:space:]]*select'; then
    echo "❌ Only SELECT queries are allowed on production"
    exit 1
fi

# Check for unsafe operations
if echo "$query" | grep -Ei 'drop|delete|update|insert|alter|create|truncate'; then
    echo "❌ Unsafe operations detected in query"
    exit 1
fi

echo "🔒 PRODUCTION DATABASE QUERY"
echo "============================"
echo "Query: $query"
echo "User: $USER"
echo "Timestamp: $(date)"
echo "Environment: PRODUCTION"
echo ""

echo "🔍 Executing SELECT query on production database..."
psql -c "$query"
""",
            args=[
                Arg(name="query", type="str", description="SELECT query to execute on production", required=True)
            ]
        )

# Initialize tools
PostgresOperations()