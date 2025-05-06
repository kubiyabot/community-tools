from kubiya_sdk.tools import Arg
from .base import AWSCliTool, AWSSdkTool
from kubiya_sdk.tools.registry import tool_registry

ec2_install_software = AWSSdkTool(
    name="ec2_install_software",
    description="Install software on an EC2 instance using SSM Run Command",
    content="""
import boto3
import time

def install_software(instance_id, software_name, command):
    ssm = boto3.client('ssm')
    
    # Check if instance is managed by SSM
    try:
        response = ssm.describe_instance_information(
            Filters=[{'Key': 'InstanceIds', 'Values': [instance_id]}]
        )
        if len(response['InstanceInformationList']) == 0:
            return {"error": f"Instance {instance_id} is not managed by SSM. Ensure SSM agent is installed and running."}
    except Exception as e:
        return {"error": f"Error checking instance SSM status: {str(e)}"}
    
    # Run the installation command
    try:
        response = ssm.send_command(
            InstanceIds=[instance_id],
            DocumentName='AWS-RunShellScript',
            Parameters={'commands': [command]},
            Comment=f'Install {software_name}'
        )
        
        command_id = response['Command']['CommandId']
        
        # Wait for command to complete
        time.sleep(2)
        
        # Get command result
        output = ssm.get_command_invocation(
            CommandId=command_id,
            InstanceId=instance_id
        )
        
        status = output['Status']
        
        # If command is still running, provide command ID for later checking
        if status in ['Pending', 'InProgress']:
            return {
                "status": status,
                "message": f"Installation of {software_name} is {status}. Check status later with command ID: {command_id}",
                "command_id": command_id
            }
        
        # Return results
        return {
            "status": status,
            "output": output['StandardOutputContent'],
            "error": output['StandardErrorContent'] if output['StandardErrorContent'] else None
        }
        
    except Exception as e:
        return {"error": f"Error running installation command: {str(e)}"}

result = install_software(instance_id, software_name, command)
return result
""",
    args=[
        Arg(name="instance_id", type="str", description="ID of the EC2 instance", required=True),
        Arg(name="software_name", type="str", description="Name of the software to install", required=True),
        Arg(name="command", type="str", description="Installation command (e.g., 'apt-get update && apt-get install -y nginx')", required=True),
    ],
    mermaid_diagram="""
    graph TD
        A[👤 User] -->|Request: Install software| B[🤖 TeamMate]
        B --> C{{"Instance and software details?" 🔢}}
        C --> D[User provides details ✍️]
        D --> E[API request to AWS SSM ☁️]
        E --> F[AWS runs command on instance 🖥️]
        F --> G[User receives installation status 📄]

        style A fill:#f0f9ff,stroke:#0369a1,stroke-width:2px;
        style B fill:#dbeafe,stroke:#3b82f6,stroke-width:2px;
        style C fill:#d1fae5,stroke:#059669,stroke-width:2px;
        style D fill:#bbf7d0,stroke:#16a34a,stroke-width:2px;
        style E fill:#fee2e2,stroke:#ef4444,stroke-width:2px;
        style F fill:#ffedd5,stroke:#ea580c,stroke-width:2px;
        style G fill:#e0f2fe,stroke:#0284c7,stroke-width:2px;
    """
)

ec2_check_command_status = AWSSdkTool(
    name="ec2_check_command_status",
    description="Check the status of a command execution on an EC2 instance",
    content="""
import boto3

def check_command_status(command_id, instance_id):
    ssm = boto3.client('ssm')
    
    try:
        output = ssm.get_command_invocation(
            CommandId=command_id,
            InstanceId=instance_id
        )
        
        return {
            "status": output['Status'],
            "output": output['StandardOutputContent'],
            "error": output['StandardErrorContent'] if output['StandardErrorContent'] else None
        }
        
    except Exception as e:
        return {"error": f"Error checking command status: {str(e)}"}

result = check_command_status(command_id, instance_id)
return result
""",
    args=[
        Arg(name="command_id", type="str", description="ID of the command execution", required=True),
        Arg(name="instance_id", type="str", description="ID of the EC2 instance", required=True),
    ],
    mermaid_diagram="""
    graph TD
        A[👤 User] -->|Request: Check command status| B[🤖 TeamMate]
        B --> C{{"Command and instance IDs?" 🔢}}
        C --> D[User provides IDs ✍️]
        D --> E[API request to AWS SSM ☁️]
        E --> F[AWS retrieves command status 🔄]
        F --> G[User receives command results 📄]

        style A fill:#f0f9ff,stroke:#0369a1,stroke-width:2px;
        style B fill:#dbeafe,stroke:#3b82f6,stroke-width:2px;
        style C fill:#d1fae5,stroke:#059669,stroke-width:2px;
        style D fill:#bbf7d0,stroke:#16a34a,stroke-width:2px;
        style E fill:#fee2e2,stroke:#ef4444,stroke-width:2px;
        style F fill:#ffedd5,stroke:#ea580c,stroke-width:2px;
        style G fill:#e0f2fe,stroke:#0284c7,stroke-width:2px;
    """
)

ec2_run_command = AWSSdkTool(
    name="ec2_run_command",
    description="Run a shell command on an EC2 instance using SSM",
    content="""
import boto3
import time

def run_command(instance_id, command):
    ssm = boto3.client('ssm')
    
    # Check if instance is managed by SSM
    try:
        response = ssm.describe_instance_information(
            Filters=[{'Key': 'InstanceIds', 'Values': [instance_id]}]
        )
        if len(response['InstanceInformationList']) == 0:
            return {"error": f"Instance {instance_id} is not managed by SSM. Ensure SSM agent is installed and running."}
    except Exception as e:
        return {"error": f"Error checking instance SSM status: {str(e)}"}
    
    # Run the command
    try:
        response = ssm.send_command(
            InstanceIds=[instance_id],
            DocumentName='AWS-RunShellScript',
            Parameters={'commands': [command]}
        )
        
        command_id = response['Command']['CommandId']
        
        # Wait for command to complete
        time.sleep(2)
        
        # Get command result
        output = ssm.get_command_invocation(
            CommandId=command_id,
            InstanceId=instance_id
        )
        
        status = output['Status']
        
        # If command is still running, provide command ID for later checking
        if status in ['Pending', 'InProgress']:
            return {
                "status": status,
                "message": f"Command is {status}. Check status later with command ID: {command_id}",
                "command_id": command_id
            }
        
        # Return results
        return {
            "status": status,
            "output": output['StandardOutputContent'],
            "error": output['StandardErrorContent'] if output['StandardErrorContent'] else None
        }
        
    except Exception as e:
        return {"error": f"Error running command: {str(e)}"}

result = run_command(instance_id, command)
return result
""",
    args=[
        Arg(name="instance_id", type="str", description="ID of the EC2 instance", required=True),
        Arg(name="command", type="str", description="Shell command to run", required=True),
    ],
    mermaid_diagram="""
    graph TD
        A[👤 User] -->|Request: Run command| B[🤖 TeamMate]
        B --> C{{"Instance ID and command?" 🔢}}
        C --> D[User provides details ✍️]
        D --> E[API request to AWS SSM ☁️]
        E --> F[AWS runs command on instance 🖥️]
        F --> G[User receives command output 📄]

        style A fill:#f0f9ff,stroke:#0369a1,stroke-width:2px;
        style B fill:#dbeafe,stroke:#3b82f6,stroke-width:2px;
        style C fill:#d1fae5,stroke:#059669,stroke-width:2px;
        style D fill:#bbf7d0,stroke:#16a34a,stroke-width:2px;
        style E fill:#fee2e2,stroke:#ef4444,stroke-width:2px;
        style F fill:#ffedd5,stroke:#ea580c,stroke-width:2px;
        style G fill:#e0f2fe,stroke:#0284c7,stroke-width:2px;
    """
)

tool_registry.register("aws", ec2_install_software)
tool_registry.register("aws", ec2_check_command_status)
tool_registry.register("aws", ec2_run_command) 