import pytest
from iac.create_resource import apply_terraform, store_state_in_db
import os
import sqlite3
import subprocess
import tempfile

def test_apply_terraform(mocker):
    tf_code = """
    provider "aws" {
      region = "us-west-2"
    }
    resource "aws_instance" "example" {
      ami = "ami-0c55b159cbfafe1f0"
      instance_type = "t2.micro"
    }
    """
    mocker.patch('subprocess.run')
    mocker.patch('aws.create_resource.store_state_in_db')
    apply_terraform("req-123", tf_code)
    subprocess.run.assert_any_call(["terraform", "init"], check=True)
    subprocess.run.assert_any_call(["terraform", "plan", "-out", "req-123.tfplan"], check=True)
    subprocess.run.assert_any_call(["terraform", "apply", "-auto-approve", "req-123.tfplan"], check=True)

def test_store_state_in_db():
    with tempfile.NamedTemporaryFile() as temp_db:
        os.environ['SQLITE_DB'] = temp_db.name
        conn = sqlite3.connect(temp_db.name)
        conn.execute('''CREATE TABLE resource_states (request_id text, state_data text)''')
        conn.commit()
        conn.close()

        state_data = '{"version": 4, "terraform_version": "0.12.24", "serial": 1, "lineage": "abcd", "outputs": {}, "resources": []}'
        store_state_in_db("req-123", state_data)

        conn = sqlite3.connect(temp_db.name)
        c = conn.cursor()
        c.execute("SELECT state_data FROM resource_states WHERE request_id=?", ("req-123",))
        row = c.fetchone()
        conn.close()
        
        assert row is not None
        assert row[0] == state_data
