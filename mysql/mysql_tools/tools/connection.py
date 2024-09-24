from kubiya import Tool
import mysql.connector
from sshtunnel import SSHTunnelForwarder

class MySQLConnection(Tool):
    def connect(self, ssh_host: str, ssh_user: str, ssh_private_key: str, 
                mysql_host: str, mysql_user: str, mysql_password: str, 
                mysql_database: str):
        """
        Connect to MySQL database through SSH tunnel.

        Parameters:
        - ssh_host: SSH server hostname
        - ssh_user: SSH username
        - ssh_private_key: Path to SSH private key file
        - mysql_host: MySQL server hostname
        - mysql_user: MySQL username
        - mysql_password: MySQL password
        - mysql_database: MySQL database name

        Returns:
        - Dict with connection and ssh_tunnel objects
        """
        ssh_tunnel = SSHTunnelForwarder(
            (ssh_host, 22),
            ssh_username=ssh_user,
            ssh_pkey=ssh_private_key,
            remote_bind_address=(mysql_host, 3306)
        )
        ssh_tunnel.start()

        connection = mysql.connector.connect(
            host='127.0.0.1',
            port=ssh_tunnel.local_bind_port,
            user=mysql_user,
            password=mysql_password,
            database=mysql_database
        )
        
        return {'connection': connection, 'ssh_tunnel': ssh_tunnel}

    def disconnect(self, connection: mysql.connector.MySQLConnection, 
                   ssh_tunnel: SSHTunnelForwarder):
        """
        Disconnect from MySQL database and close SSH tunnel.

        Parameters:
        - connection: MySQL connection object
        - ssh_tunnel: SSH tunnel object

        Returns:
        - Dict with disconnection status
        """
        connection.close()
        ssh_tunnel.stop()
        return {'status': 'disconnected'}

mysql_connect = MySQLConnection().connect
mysql_disconnect = MySQLConnection().disconnect