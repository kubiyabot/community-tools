from kubiya_sdk.tools import Arg
from .base import ReportTool
from kubiya_sdk.tools.registry import tool_registry


create_es_watchers = ReportTool(
    name="create_es_watchers",
    description="Create Elasticsearch watchers for organizations",
    content="""
import requests
import json
import os
import boto3

# Set up the correct Elasticsearch URL
ES_URL = "https://kubiya-dev-eu-west-1.es.eu-west-1.aws.found.io:9243"
KB_URL = "https://kubiya-dev-eu-west-1.kb.eu-west-1.aws.found.io:9243"
HEADERS = {"Content-Type": "application/json"}

# Get Kibana credentials from environment variables
USERNAME = os.getenv("ES_USER")
PASSWORD = os.getenv("ES_PASS")

if not USERNAME or not PASSWORD:
    raise EnvironmentError("ES_USER or ES_PASS environment variables are not set.")

def download_organizations_file(bucket_name, file_name, local_file_path):
    s3 = boto3.client('s3')
    s3.download_file(bucket_name, file_name, local_file_path)
    print(f"Downloaded {file_name} from bucket {bucket_name} to {local_file_path}")

def get_organizations_from_file(file_path):
    organizations = []
    with open(file_path, 'r') as file:
        for line in file.readlines():
            org, email = line.strip().split(',')
            organizations.append({'name': org, 'email': email})
    return organizations

def watcher_exists(watcher_name):
    url = f"{ES_URL}/_watcher/watch/{watcher_name}"
    response = requests.get(url, auth=(USERNAME, PASSWORD), headers=HEADERS)
    return response.status_code == 200

def create_watcher(org_name, email):
    watcher_name = f"{org_name}_report"
    if watcher_exists(watcher_name):
        print(f"Watcher for {org_name} already exists.")
        return

    dashboard_url = (
        f"{KB_URL}/api/reporting/generate/printablePdfV2?jobParams=%28"
        f"browserTimezone%3AAsia%2FJerusalem%2Clayout%3A%28dimensions%3A%28height%3A2528%2Cwidth%3A2048%29%2C"
        f"id%3Apreserve_layout%29%2ClocatorParams%3A%21%28%28id%3ADASHBOARD_APP_LOCATOR%2Cparams%3A%28"
        f"dashboardId%3A%276765bc60-6f42-11ef-9797-6f84672456d8%27%2Cfilters%3A%21%28%28meta%3A%28"
        f"key%3A%27org%27%2Cvalue%3A%27{org_name}%27%29%2Cquery%3A%28match_phrase%3A%28org%3A%27"
        f"{org_name}%27%29%29%29%29%2CpreserveSavedFilters%3A%21t%2CtimeRange%3A%28from%3A%272024-08-27T06%3A00%3A00.000Z%27%2C"
        f"to%3A%272024-08-28T06%3A00%3A00.000Z%27%29%2CuseHash%3A%21f%2CviewMode%3Aview%29%29%29%2C"
        f"objectType%3Adashboard%2Ctitle%3A%27Evgeniy%20MASTER-test%27%2Cversion%3A%278.7.0%27%29"
    )

    watcher_payload = {
        "trigger": {
            "schedule": {
                "weekly": [
                    {"on": "monday", "at": "18:00"},
                    {"on": "tuesday", "at": "18:00"},
                    {"on": "wednesday", "at": "18:00"},
                    {"on": "thursday", "at": "18:00"},
                    {"on": "friday", "at": "18:00"}
                ]
            }
        },
        "actions": {
            "email_admin": {
                "email": {
                    "to": f"'{org_name} Admin <{email}>'",
                    "subject": f"{org_name}'s Usage Report",
                    "attachments": {
                        f"{org_name}_report.pdf": {
                            "reporting": {
                                "url": dashboard_url,
                                "retries": 3,
                                "interval": "90s",
                                "auth": {
                                    "basic": {
                                        "username": USERNAME,
                                        "password": PASSWORD
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    print(watcher_name)
    url = f"{ES_URL}/_watcher/watch/{watcher_name}"
    response = requests.put(url, auth=(USERNAME, PASSWORD), headers=HEADERS, data=json.dumps(watcher_payload))

    if response.status_code == 201:
        print(f"Successfully created watcher for {org_name}")
    else:
        print(f"Failed to create watcher for {org_name}: {response.status_code} - {response.text}")

bucket_name = 'elastic-search-reports'
file_name = 'organizations.txt'
local_file_path = 'organizations.txt'

download_organizations_file(bucket_name, file_name, local_file_path)

organizations = get_organizations_from_file(local_file_path)
for org in organizations:
    create_watcher(org['name'], org['email'])
    """,
    args=[],
    mermaid_diagram="""
    graph TD
        A[👤 User] -->|Request: Create ES Watchers| B[🤖 TeamMate]
        B --> C[Download organizations file from S3]
        C --> D[Read organizations from file]
        D --> E[Create watchers for each organization]
        E --> F[User receives creation status]

        style A fill:#f0f9ff,stroke:#0369a1,stroke-width:2px;
        style B fill:#dbeafe,stroke:#3b82f6,stroke-width:2px;
        style C fill:#d1fae5,stroke:#059669,stroke-width:2px;
        style D fill:#bbf7d0,stroke:#16a34a,stroke-width:2px;
        style E fill:#fee2e2,stroke:#ef4444,stroke-width:2px;
        style F fill:#e0f2fe,stroke:#0284c7,stroke-width:2px;
    """
)

tool_registry.register("report", create_es_watchers)
