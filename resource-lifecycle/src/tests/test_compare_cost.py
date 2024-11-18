import pytest
from iac.compare_cost import compare_cost_with_avg, get_average_monthly_cost

def test_compare_cost_with_avg_greater(mocker):
    mocker.patch('aws.compare_cost.get_average_monthly_cost', return_value=100.0)
    comparison_result = compare_cost_with_avg(120.0)
    assert comparison_result == "greater"

def test_compare_cost_with_avg_less(mocker):
    mocker.patch('aws.compare_cost.get_average_monthly_cost', return_value=100.0)
    comparison_result = compare_cost_with_avg(80.0)
    assert comparison_result == "less"

def test_get_average_monthly_cost(mocker):
    mocker.patch('boto3.Session.client')
    mock_client = mocker.patch('aws.compare_cost.get_average_monthly_cost')
    mock_client.return_value.get_cost_and_usage.return_value = {
        'ResultsByTime': [{'Total': {'BlendedCost': {'Amount': '300.0'}}}]
    }
    average_monthly_cost = get_average_monthly_cost("default")
    assert average_monthly_cost == 100.0
