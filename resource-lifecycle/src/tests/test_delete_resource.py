import pytest
from iac.delete_resource import delete_resource
import subprocess
import os
import sqlite3
import tempfile

def test_delete_resource(mocker):
    state_data = '{"version": 4, "terraform_version": "0.12.24", "serial": 1, "lineage": "abcd", "outputs": {}, "resources": []}'
    with tempfile.NamedTemporaryFile() as temp_db:
        os.environ['SQLITE_DB'] = temp_db.name
        conn = sqlite3.connect(temp_db.name)
        conn.execute('''CREATE TABLE resource_states (request_id text, state_data text)''')
        conn.execute("INSERT INTO resource_states (request_id, state_data) VALUES (?, ?)", ("req-123", state_data))
        conn.commit()
        conn.close()

        mocker.patch('subprocess.run')
        delete_resource("req-123")
        subprocess.run.assert_any_call(["terraform", "init"], check=True)
        subprocess.run.assert_any_call(["terraform", "destroy", "-auto-approve"], check=True)
