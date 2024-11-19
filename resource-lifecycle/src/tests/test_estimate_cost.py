import pytest
from llm.estimate_cost import estimate_resource_cost
import json

def test_estimate_resource_cost(mocker):
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
    mocker.patch('llm.estimate_cost.open', mocker.mock_open(read_data=json.dumps({
        'projects': [{'totalMonthlyCost': 20.0}]
    })), create=True)
    estimated_cost = estimate_resource_cost(tf_code)
    assert estimated_cost == 20.0
