import os
import sys
from mem0 import Memory
from typing import Optional, Dict, Any, List

# Add scripts directory to Python path for config import
scripts_dir = os.path.dirname(os.path.abspath(__file__))
if scripts_dir not in sys.path:
    sys.path.append(scripts_dir)

from config import MemoryConfig

def find_preference(search_query: str) -> None:
    """
    Search for specific preferences using the provided query.
    Uses both vector and graph-based search for comprehensive results.
    
    Args:
        search_query: Text to search for in preferences
    """
    try:
        if not search_query.strip():
            raise ValueError("Search query cannot be empty")

        # Get configuration
        config = MemoryConfig.get_neo4j_config()
        
        # Initialize Memory client
        m = Memory.from_config(config_dict=config)
        
        # Get user ID
        user_id = MemoryConfig.get_user_id()

        print(f"🔍 Searching for preferences matching '{search_query}'...")

        try:
            # Try using the graph-enhanced search method first
            search_results = m.search(
                query=search_query, 
                user_id=user_id,
                include_graph=True  # Enable graph-based search
            )
            
            if search_results and isinstance(search_results, dict):
                memories = []
                
                # Handle vector search results
                if search_results.get('results'):
                    memories.extend([
                        MemoryConfig.format_memory_response(mem) 
                        for mem in search_results['results']
                    ])
                
                # Handle graph search results
                if search_results.get('graph_results'):
                    for result in search_results['graph_results']:
                        formatted = MemoryConfig.format_memory_response(result)
                        if formatted not in memories:  # Avoid duplicates
                            memories.append(formatted)
            else:
                # Fallback to get_all and filter manually
                raw_memories = m.get_all(user_id=user_id)
                memories = [
                    MemoryConfig.format_memory_response(mem) 
                    for mem in (raw_memories if isinstance(raw_memories, list) 
                              else raw_memories.get('memories', []))
                ]
                
        except Exception as e:
            print(f"⚠️ Advanced search failed, falling back to basic search: {str(e)}")
            raw_memories = m.get_all(user_id=user_id)
            memories = [
                MemoryConfig.format_memory_response(mem) 
                for mem in (raw_memories if isinstance(raw_memories, list) 
                          else raw_memories.get('memories', []))
            ]
        
        if not memories:
            print("📭 No stored preferences found.")
            return

        # Perform search if using manual filtering
        search_terms = search_query.lower().split()
        matches = []
        
        for mem in memories:
            content = mem['content'].lower()
            tags = [tag.lower() for tag in mem['metadata'].get('tags', [])]
            entities = [str(entity).lower() for entity in mem.get('entities', [])]
            
            # Calculate match score based on content, tags, and entities
            score = sum(
                1 for term in search_terms 
                if term in content 
                or any(term in tag for tag in tags)
                or any(term in entity for entity in entities)
            )
            
            if score > 0:
                matches.append((score, mem))

        if not matches:
            print("🤔 No matching preferences found.")
            print("\n💡 Tips for better search:")
            print("- Try using different keywords")
            print("- Check for typos")
            print("- Use broader terms")
            print("\n📋 Use 'load_memories' to see all your preferences")
            return

        # Sort by score (most relevant first)
        matches.sort(reverse=True, key=lambda x: x[0])
        
        print(f"\n✨ Found {len(matches)} matching preferences:\n")
        for score, mem in matches:
            tags = mem['metadata'].get('tags', [])
            tags_str = f"[{', '.join(tags)}]" if tags else "[]"
            
            print(f"📌 {mem['content']}")
            print(f"   ID: {mem['id']}")
            print(f"   Tags: {tags_str}")
            
            # Display extracted entities if available
            if mem.get('entities'):
                print(f"   Entities: {', '.join(str(e) for e in mem['entities'])}")
            
            # Display relationships if available
            if mem.get('relationships'):
                print("   Relationships:")
                for rel in mem['relationships']:
                    print(f"      - {rel}")
            
            print(f"   Added: {mem['timestamp']}\n")

    except ValueError as e:
        print(f"❌ {str(e)}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: find_preference_handler.py <search_query>")
        sys.exit(1)
    find_preference(sys.argv[1]) 