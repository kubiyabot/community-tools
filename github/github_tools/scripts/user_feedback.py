
from mem0 import MemoryClient  # Uncomment this line to use MemoryClient
import sys  # Import sys for command-line arguments


def evaluate_user_performance(user_email, query):
    """
    Evaluates the user's performance based on their previous interactions.

    Args:
        user_email (str): The email of the user.
        query (str): The question or query to evaluate.

    Returns:
        None
    """
    # Initialize Mem0 client
    memory_client = MemoryClient(api_key="m0-7TIHSrRBHv1CNO6bvsjQUEEsc5kguHhesNFMjdwN")

    # Search for previous interactions
    results = memory_client.search(query, user_id=user_email)

    # Process and return the results
    if results:
        for result in results:
            print(result)  # Adjust this line to format the output as needed
    else:
        print(f"No previous interactions found for user {user_email} on query '{query}'.")

def main():
    """
    Main function to execute the user performance evaluation.
    """
    try:
        # Get variables from environment
        required_vars = [
            'USER_EMAIL'
        ]
        
        variables = {}
        for var in required_vars:
            if var not in os.environ:
                print(f"Missing required environment variable: {var}")
                raise KeyError(f"Missing required environment variable: {var}")
            variables[var.lower()] = os.environ[var]

        evaluate_user_performance(variables['user_email'], variables['query'])  # Uncommented and adjusted

        print("User performance evaluation completed successfully")
        
    except KeyError as e:
        print(f"Missing environment variable: {str(e)}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()  # Call the main function to execute the script