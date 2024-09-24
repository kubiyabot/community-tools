import unittest
from unittest.mock import MagicMock
from mysql_tools.tools.query import MySQLQuery

class TestMySQLQuery(unittest.TestCase):
    def setUp(self):
        self.mock_connection = MagicMock()
        self.mock_cursor = MagicMock()
        self.mock_connection.cursor.return_value = self.mock_cursor

    def test_execute_query(self):
        query_tool = MySQLQuery()
        result = query_tool.execute_query(
            connection=self.mock_connection,
            query='INSERT INTO test_table (column1) VALUES ("test")'
        )

        self.assertEqual(result, {'status': 'query executed'})
        self.mock_connection.cursor.assert_called_once()
        self.mock_cursor.execute.assert_called_once_with('INSERT INTO test_table (column1) VALUES ("test")')
        self.mock_connection.commit.assert_called_once()
        self.mock_cursor.close.assert_called_once()

    def test_fetch_results(self):
        self.mock_cursor.fetchall.return_value = [{'id': 1, 'name': 'Test'}]

        query_tool = MySQLQuery()
        result = query_tool.fetch_results(
            connection=self.mock_connection,
            query='SELECT * FROM test_table'
        )

        self.assertEqual(result, {'results': [{'id': 1, 'name': 'Test'}]})
        self.mock_connection.cursor.assert_called_once_with(dictionary=True)
        self.mock_cursor.execute.assert_called_once_with('SELECT * FROM test_table')
        self.mock_cursor.fetchall.assert_called_once()
        self.mock_cursor.close.assert_called_once()

if __name__ == '__main__':
    unittest.main()