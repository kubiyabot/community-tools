import unittest
from unittest.mock import patch, MagicMock
from mysql_tools.tools.connection import MySQLConnection

class TestMySQLConnection(unittest.TestCase):
    @patch('mysql_tools.tools.connection.SSHTunnelForwarder')
    @patch('mysql_tools.tools.connection.mysql.connector.connect')
    def test_connect(self, mock_connect, mock_ssh_tunnel):
        mock_ssh_tunnel.return_value.local_bind_port = 12345
        mock_connection = MagicMock()
        mock_connect.return_value = mock_connection

        connection_tool = MySQLConnection()
        result = connection_tool.connect(
            ssh_host='ssh.example.com',
            ssh_user='ssh_user',
            ssh_private_key='/path/to/key',
            mysql_host='mysql.example.com',
            mysql_user='db_user',
            mysql_password='password',
            mysql_database='testdb'
        )

        self.assertIn('connection', result)
        self.assertIn('ssh_tunnel', result)
        mock_ssh_tunnel.assert_called_once()
        mock_connect.assert_called_once_with(
            host='127.0.0.1',
            port=12345,
            user='db_user',
            password='password',
            database='testdb'
        )

    def test_disconnect(self):
        mock_connection = MagicMock()
        mock_ssh_tunnel = MagicMock()

        connection_tool = MySQLConnection()
        result = connection_tool.disconnect(
            connection=mock_connection,
            ssh_tunnel=mock_ssh_tunnel
        )

        self.assertEqual(result, {'status': 'disconnected'})
        mock_connection.close.assert_called_once()
        mock_ssh_tunnel.stop.assert_called_once()

if __name__ == '__main__':
    unittest.main()