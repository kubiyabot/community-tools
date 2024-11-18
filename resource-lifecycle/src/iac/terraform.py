import os
import subprocess
import logging
import requests
import sqlite3
import json
from typing import Tuple, Dict
from pytimeparse.timeparse import timeparse

# Set environment variables and defaults
SHOW_TF_OUTPUT = os.getenv("SHOW_TF_OUTPUT", "true").lower() == "true"
LOGS_PATH = os.getenv("LOGS_PATH", "/tf_logs")
LOGS_ENABLED = os.getenv("LOGS_ENABLED", "false").lower() == "true"
GENERATE_GRAPH = os.getenv("GENERATE_GRAPH", "false").lower() == "true"  # requires Graphviz, see https://graphviz.org/download/
SLACK_CHANNEL_ID = os.getenv("SLACK_CHANNEL_ID")
SLACK_THREAD_TS = os.getenv("SLACK_THREAD_TS")
SLACK_API_TOKEN = os.getenv("SLACK_API_TOKEN")
MAX_TTL = os.getenv('MAX_TTL', '30d')

# Configure logging based on LOGS_ENABLED
if LOGS_ENABLED:
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
else:
    logging.basicConfig(level=logging.INFO, format='%(message)s')

COMMON_ERRORS = {
    "resource already exists": "Resource with the given name already exists.",
    "insufficient permissions": "Insufficient permissions to perform this operation.",
    "network issue": "Network issue encountered during operation.",
    "invalid credentials": "Invalid AWS credentials provided.",
    "out of memory": "Out of memory error occurred.",
}

def run_terraform_command(command: list, silent=False) -> Tuple[bool, str]:
    # Print the command being run
    print(f"🏃 {' '.join(command)}")

    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    stdout_lines = []
    stderr_lines = []

    if not silent:
        for stdout_line in iter(process.stdout.readline, ""):
            stdout_lines.append(stdout_line.strip())
            filter_and_print(stdout_line.strip())

        for stderr_line in iter(process.stderr.readline, ""):
            stderr_lines.append(stderr_line.strip())
            filter_and_print(stderr_line.strip(), is_error=True)
        
        process.stdout.close()
        process.stderr.close()
        process.wait()

        if process.returncode == 0:
            return True, "\n".join(stdout_lines)
        else:
            error_output = "\n".join(stderr_lines)
            specific_error = check_common_errors(error_output)
            return False, specific_error

    else:
        stdout, stderr = process.communicate()
        process.wait()
        if process.returncode == 0:
            return True, stdout
        else:
            specific_error = check_common_errors(stderr)
            return False, specific_error

def filter_and_print(line: str, is_error: bool = False) -> None:
    filtered_line = filter_terraform_output(line)
    if filtered_line:
        if is_error:
            print(filtered_line)
        else:
            print(filtered_line)

def filter_terraform_output(line: str) -> str:
    keywords = ["Plan:", "Changes to", "Apply complete", "resource", "Error:", "Warning:"]
    for keyword in keywords:
        if keyword in line:
            return line
    return None

def check_common_errors(error_output: str) -> str:
    for error_key, error_message in COMMON_ERRORS.items():
        if error_key in error_output.lower():
            return error_message
    return error_output

def prepare_plan_path(request_id: str) -> str:
    plan_path = f"/tf_plans/{request_id}/"
    os.makedirs(plan_path, exist_ok=True)
    return plan_path

def write_tf_files(tf_files: Dict[str, str], plan_path: str) -> None:
    for filename, content in tf_files.items():
        filepath = os.path.join(plan_path, filename)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "w") as tf_file:
            tf_file.write(content)

def create_terraform_plan(tf_files: Dict[str, str], request_id: str) -> Tuple[bool, str, str]:
    plan_path = prepare_plan_path(request_id)
    write_tf_files(tf_files, plan_path)

    os.chdir(plan_path)
    os.environ["TF_IN_AUTOMATION"] = "true"
    os.environ["TF_CLI_ARGS"] = "-no-color"

    try:
        success, output = run_terraform_command(['terraform', 'init'])
        if not success:
            return False, output, None

        success, plan_output = run_terraform_command(['terraform', 'plan', '-out', f'{request_id}.tfplan'], silent=False)
        if not success:
            return False, plan_output, None

        success, plan_json = run_terraform_command(['terraform', 'show', '-json', f'{request_id}.tfplan'], silent=True)
        if not success:
            return False, plan_json, None

        if GENERATE_GRAPH:
            graph_path = generate_graph(plan_path, request_id, use_state=True)
            send_graph_to_slack(graph_path, request_id, "👇 Here's a preview of the Terraform plan")

        # Send files to Slack
        send_files_to_slack(tf_files, plan_output, request_id)
        print(f"Terraform project files and plan output sent to Slack.")

        return True, plan_output, plan_json
    except subprocess.CalledProcessError as e:
        error_output = e.stderr.decode('utf-8')
        logging.error(f"Error creating Terraform plan: {error_output}")
        specific_error = check_common_errors(error_output)
        return False, f"Error creating Terraform plan: {specific_error}", None

def apply_terraform(tf_files: Dict[str, str], request_id: str, apply: bool = False) -> Tuple[str, str]:
    plan_path = prepare_plan_path(request_id)
    write_tf_files(tf_files, plan_path)

    os.chdir(plan_path)
    os.environ["TF_IN_AUTOMATION"] = "true"
    os.environ["TF_CLI_ARGS"] = "-no-color"

    success, output = run_terraform_command(['terraform', 'init'])
    if not success:
        raise subprocess.CalledProcessError(returncode=1, cmd='terraform init', output=output)

    success, plan_output = run_terraform_command(['terraform', 'plan', '-out', f'{request_id}.tfplan'], silent=True)
    if not success:
        raise subprocess.CalledProcessError(returncode=1, cmd='terraform plan', output=plan_output)

    if apply:
        success, apply_output = run_terraform_command(['terraform', 'apply', '-auto-approve', f'{request_id}.tfplan'])
        if not success:
            raise subprocess.CalledProcessError(returncode=1, cmd='terraform apply', output=apply_output)

        log_path = os.path.join(LOGS_PATH, request_id)
        os.makedirs(log_path, exist_ok=True)
        with open(os.path.join(log_path, "apply.log"), "w") as log_file:
            log_file.write(apply_output)

        return apply_output, plan_path

    return "Plan created but not applied.", plan_path

def destroy_terraform(request_id: str) -> str:
    conn = sqlite3.connect('/sqlite_data/approval_requests.db')
    c = conn.cursor()

    c.execute("SELECT tf_state, resource_details FROM resources WHERE request_id = ?", (request_id,))
    result = c.fetchone()
    conn.close()

    if result is None:
        error_message = f"No Terraform state found for request ID {request_id}."
        logging.error(error_message)
        raise ValueError(error_message)

    tf_state, resource_details = result
    resource_details = json.loads(resource_details)

    plan_path = prepare_plan_path(request_id)
    write_tf_files(resource_details["tf_files"], plan_path)

    # Write the state file
    state_file_path = os.path.join(plan_path, "terraform.tfstate")
    with open(state_file_path, "w") as state_file:
        state_file.write(tf_state)

    os.chdir(plan_path)
    os.environ["TF_IN_AUTOMATION"] = "true"
    os.environ["TF_CLI_ARGS"] = "-no-color"

    success, output = run_terraform_command(['terraform', 'init'])
    if not success:
        raise subprocess.CalledProcessError(returncode=1, cmd='terraform init', output=output)

    success, destroy_output = run_terraform_command(['terraform', 'destroy', '-auto-approve'])
    if not success:
        raise subprocess.CalledProcessError(returncode=1, cmd='terraform destroy', output=destroy_output)

    log_path = os.path.join(LOGS_PATH, request_id)
    os.makedirs(log_path, exist_ok=True)
    with open(os.path.join(log_path, "destroy.log"), "w") as log_file:
        log_file.write(destroy_output)
    return destroy_output

def generate_graph(plan_path: str, request_id: str, use_state: bool) -> str:
    print("📊 Generating graph representation..")
    dot_file = os.path.join(plan_path, f'{request_id}.dot')
    png_file = os.path.join(plan_path, f'{request_id}.png')

    # Generate the DOT file using terraform graph
    command = ['terraform', 'graph']

    with open(dot_file, 'w') as file:
        subprocess.run(command, stdout=file, cwd=plan_path, check=True)

    # Convert the DOT file to PNG using Graphviz
    command = ['dot', '-Tpng', dot_file, '-o', png_file]
    subprocess.run(command, check=True)
    print(f"📊 Graph generated.. sending")
    return png_file

def send_graph_to_slack(graph_path: str, request_id: str, message: str) -> None:
    with open(graph_path, 'rb') as file:
        response = requests.post(
            "https://slack.com/api/files.upload",
            headers={
                'Authorization': f'Bearer {os.getenv("SLACK_API_TOKEN")}'
            },
            data={
                'channels': SLACK_CHANNEL_ID,
                'thread_ts': SLACK_THREAD_TS,
                'initial_comment': f"{message}",
            },
            files={
                'file': file
            }
        )

    if response.status_code >= 300:
        if os.getenv('KUBIYA_DEBUG'):
            print(f"Error uploading graph to Slack: {response.status_code} - {response.text}")

# Function to parse TTL and handle errors
def parse_ttl(ttl: str) -> int:
    ttl_seconds = timeparse(ttl)
    if ttl_seconds is None:
        raise ValueError(f"Invalid TTL format: {ttl}")
    return ttl_seconds

def send_files_to_slack(tf_files: Dict[str, str], plan_output: str, request_id: str) -> None:
    # Send the Terraform files and plan output to Slack
    #for filename, content in tf_files.items():
        #send_file_to_slack(content, filename, request_id)

    send_file_to_slack(plan_output, "terraform_plan_output.txt", request_id)

def send_file_to_slack(file_content: str, filename: str, request_id: str) -> None:
    response = requests.post(
        "https://slack.com/api/files.upload",
        headers={
            'Authorization': f'Bearer {SLACK_API_TOKEN}'
        },
        data={
            'channels': SLACK_CHANNEL_ID,
            'thread_ts': SLACK_THREAD_TS,
            'initial_comment': f"File related to request {request_id}: {filename}",
            'filename': filename,
        },
        files={
            'file': (filename, file_content)
        }
    )

    if response.status_code >= 300:
        logging.error(f"Error uploading file to Slack: {response.status_code} - {response.text}")
        if os.getenv('KUBIYA_DEBUG'):
            print(f"Error uploading file to Slack: {response.status_code} - {response.text}")
