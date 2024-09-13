from kubiya import Tool
from typing import List, Dict, Any
import mysql.connector

class MySQLQuery(Tool):
    def execute_query(self, connection: mysql.connector.MySQLConnection, 
                      query: str) -> Dict[str, str]:
        """
        Execute a MySQL query.

        Parameters:
        - connection: MySQL connection object
        - query: SQL query string to execute

        Returns:
        - Dict with status of query execution
        """
        cursor = connection.cursor()
        cursor.execute(query)
        connection.commit()
        cursor.close()
        
        return {'status': 'query executed'}

    def fetch_results(self, connection: mysql.connector.MySQLConnection, 
                      query: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        Execute a MySQL query and fetch the results.

        Parameters:
        - connection: MySQL connection object
        - query: SQL query string to execute

        Returns:
        - Dict with query results
        """
        cursor = connection.cursor(dictionary=True)
        cursor.execute(query)
        results = cursor.fetchall()
        cursor.close()
        
        return {'results': results}

mysql_execute_query = MySQLQuery().execute_query
mysql_fetch_results = MySQLQuery().fetch_results