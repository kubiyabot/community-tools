import os
import subprocess
import tempfile
from typing import Tuple, Dict
import json


def estimate_resource_cost(tf_plan_json: str) -> Tuple[float, Dict]:
    with tempfile.TemporaryDirectory() as temp_dir:
        plan_file = os.path.join(temp_dir, "plan.json")
        with open(plan_file, 'w') as f:
            f.write(tf_plan_json)

        try:
            infracost_output = subprocess.run(
                ["infracost", "breakdown", "--path", plan_file, "--format", "json"],
                check=True,
                capture_output=True,
                cwd=temp_dir
            )
            cost_data = json.loads(infracost_output.stdout)
            estimated_cost = float(cost_data.get('projects', [{}])[0].get('breakdown', {}).get('totalMonthlyCost', 0) or 0)
            return estimated_cost, cost_data
        except subprocess.CalledProcessError as e:
            error_message = e.stderr.decode('utf-8')
            print(f"Error running Infracost: {error_message}")
            raise RuntimeError(f"Infracost command failed: {error_message}")
        except (KeyError, IndexError, ValueError, json.JSONDecodeError) as e:
            print(f"Error parsing cost data: {e}")
            raise ValueError(f"Failed to parse cost data: {e}")


def format_cost(cost: float) -> str:
    return f"${cost:,.2f}"


def format_cost_change(cost: float) -> str:
    if cost > 0:
        return f":arrow_up: {format_cost(cost)} :money_with_wings:"
    elif cost < 0:
        return f":arrow_down: {format_cost(cost)} :chart_with_downwards_trend:"
    else:
        return format_cost(cost)


def format_cost_data_for_slack(cost_data: Dict) -> Dict:
    total_cost = float(cost_data.get('projects', [{}])[0].get('breakdown', {}).get('totalMonthlyCost', 0) or 0)
    resources = cost_data.get('projects', [{}])[0].get('breakdown', {}).get('resources', [])

    blocks = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Estimated Monthly Cost:* {format_cost(total_cost)} :moneybag:"
            }
        },
        {"type": "divider"}
    ]

    for resource in resources:
        resource_name = resource.get('name', 'Unknown Resource')
        resource_type = resource.get('resourceType', 'Unknown Type')
        monthly_cost = float(resource.get('monthlyCost', 0) or 0)
        hourly_cost = float(resource.get('hourlyCost', 0) or 0)
        cost_components = resource.get('costComponents', [])

        components_text = "\n".join([
            f"  - *{component.get('name', 'Unknown Component')}*: {format_cost_change(float(component.get('monthlyCost', 0) or 0))} per {component.get('unit', 'unit')}"
            for component in cost_components
        ])

        resource_block = {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": (
                    f"*{resource_name} ({resource_type})*\n"
                    f"Hourly: {format_cost(hourly_cost)}\n"
                    f"Monthly: {format_cost_change(monthly_cost)}\n"
                    f"*Cost Components:*\n{components_text}"
                )
            }
        }

        blocks.extend([resource_block, {"type": "divider"}])

    return {"blocks": blocks}


def main(tf_plan_json: str):
    try:
        estimated_cost, cost_data = estimate_resource_cost(tf_plan_json)
        print(f"Calculated estimated monthly cost: {format_cost(estimated_cost)}")
        slack_message = format_cost_data_for_slack(cost_data)
        print(json.dumps(slack_message, indent=2))
    except Exception as e:
        print(f"❌ An error occurred: {e}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Estimate the cost of a resource using Terraform and Infracost.')
    parser.add_argument('tf_plan_json', type=str, help='The Terraform plan JSON as a string')

    args = parser.parse_args()
    main(args.tf_plan_json)
