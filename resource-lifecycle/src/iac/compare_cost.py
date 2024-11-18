# iac/compare_cost.py

import boto3
import sys
from datetime import datetime, timedelta

def compare_cost_with_avg(estimated_cost):
    average_monthly_cost = get_average_monthly_cost()

    comparison_result = "greater" if estimated_cost >= average_monthly_cost * 1.10 else "less"
    return comparison_result

def get_average_monthly_cost():
    try:
        session = boto3.Session()
        client = session.client('ce')

        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')

        response = client.get_cost_and_usage(
            TimePeriod={'Start': start_date, 'End': end_date},
            Granularity='MONTHLY',
            Metrics=['BlendedCost']
        )

        total_cost = 0
        for result in response['ResultsByTime']:
            total_cost += float(result['Total']['BlendedCost']['Amount'])

        average_monthly_cost = total_cost / 3
        return average_monthly_cost

    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Compare estimated cost with average monthly cost.')
    parser.add_argument('estimated_cost', type=float, help='The estimated cost of the resource')

    args = parser.parse_args()
    result = compare_cost_with_avg(args.estimated_cost)
    print(f"Comparison result: {result}")
