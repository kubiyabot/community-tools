import os
from neo4j import GraphDatabase
from typing import Optional

def init_neo4j_db(uri: str, username: str, password: str, database: Optional[str] = "neo4j"):
    """Initialize Neo4j database with required schema."""
    
    driver = GraphDatabase.driver(uri, auth=(username, password))
    
    # Cypher queries to set up schema
    setup_queries = [
        # Create constraints
        """
        CREATE CONSTRAINT memory_id IF NOT EXISTS
        FOR (m:Memory) REQUIRE m.memory_id IS UNIQUE
        """,
        
        """
        CREATE CONSTRAINT user_id IF NOT EXISTS
        FOR (u:User) REQUIRE u.user_id IS UNIQUE
        """,
        
        # Create indexes
        """
        CREATE INDEX memory_content IF NOT EXISTS
        FOR (m:Memory) ON (m.content)
        """,
        
        """
        CREATE INDEX memory_timestamp IF NOT EXISTS
        FOR (m:Memory) ON (m.timestamp)
        """,
        
        # Set up property existence constraints
        """
        CREATE CONSTRAINT memory_required IF NOT EXISTS
        FOR (m:Memory) REQUIRE m.content IS NOT NULL
        """,
    ]
    
    with driver.session(database=database) as session:
        for query in setup_queries:
            try:
                session.run(query)
            except Exception as e:
                print(f"Warning during schema setup: {str(e)}")
    
    driver.close()

if __name__ == "__main__":
    # Get Neo4j credentials from environment
    uri = os.environ["NEO4J_URI"]
    username = os.environ["NEO4J_USER"]
    password = os.environ["NEO4J_PASSWORD"]
    
    init_neo4j_db(uri, username, password) 