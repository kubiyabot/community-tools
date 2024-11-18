import pytest
from llm.parse_request import parse_user_request, validate_json_structure

def test_validate_json_structure_valid():
    json_data = '{"resource_details": {"resource_id": "example-id", "type": "ec2", "size": "t2.micro", "region": "us-west-2", "other_attributes": ""}, "request_id": "req-123", "vendor": "aws"}'
    is_valid, result = validate_json_structure(json_data)
    assert is_valid
    assert isinstance(result, dict)

def test_validate_json_structure_invalid():
    json_data = '{"invalid_field": "invalid_value"}'
    is_valid, result = validate_json_structure(json_data)
    assert not is_valid
    assert result == "MISSING_DETAILS"

def test_parse_user_request(mocker):
    mocker.patch('llm.parse_request.completion', return_value={'choices': [{'text': '{"request_id": "req-123", "resource_details": {"resource_id": "example-id", "type": "ec2", "size": "t2.micro", "region": "us-west-2", "other_attributes": ""}, "vendor": "aws"}'}]})
    user_input = "Create an EC2 instance of type t2.micro in us-west-2 region"
    result, error = parse_user_request(user_input)
    assert result is not None
    assert error is None
    assert result["request_id"] == "req-123"
    assert result["resource_details"]["resource_id"] == "example-id"
