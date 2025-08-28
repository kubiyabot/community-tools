#!/usr/bin/env python
import os
import json
import logging
import sys
from kubernetes import client as k8s_client, config as k8s_config

# Ensure the package path is recognized if running script directly
# The WORKDIR in Dockerfile.discover_tool is /kubiya_tool_app
sys.path.insert(0, '/kubiya_tool_app')

from serverless_mcp.serverless_mcp_tools.discovery import discover_mcp_tools_from_config
from serverless_mcp.serverless_mcp_tools.base_tool import ServerlessMCPTool

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("DiscoverAndDefineMCPToolsScript")

# Path to the config file copied into the Docker image
CONFIG_FILE_PATH = "/kubiya_tool_app/serverless_mcp/config/servers_to_sync.json"

# -------------------------------------------------------------------------------------
# Helper: Ensure Kubernetes Deployment Exists (Deploy Mode)
# -------------------------------------------------------------------------------------

def ensure_k8s_deployment(server_cfg: dict):
    """Create or validate a Deployment (and Service) for the MCP server in the kubiya namespace."""
    namespace = os.getenv("KUBIYA_K8S_NAMESPACE", "kubiya")
    deployment_name = f"mcp-{server_cfg['id'].lower()}"
    service_name = deployment_name

    # Attempt to load in-cluster config; fallback to kubeconfig for local testing
    try:
        k8s_config.load_incluster_config()
        logger.info("Loaded in-cluster Kubernetes configuration.")
    except Exception as e:
        logger.warning(f"In-cluster config not available ({e}); attempting default kubeconfig...")
        try:
            k8s_config.load_kube_config()
        except Exception as e2:
            logger.error(f"Failed to load Kubernetes configuration: {e2}")
            return False

    apps_api = k8s_client.AppsV1Api()
    core_api = k8s_client.CoreV1Api()

    # Check if deployment exists
    try:
        apps_api.read_namespaced_deployment(name=deployment_name, namespace=namespace)
        logger.info(f"Deployment '{deployment_name}' already exists in namespace '{namespace}'. Skipping creation.")
    except k8s_client.exceptions.ApiException as api_exc:
        if api_exc.status == 404:
            logger.info(f"Creating Deployment '{deployment_name}' in namespace '{namespace}'.")
            # Start with base environment variables
            env_vars = [
                k8s_client.V1EnvVar(name="GIT_REPO_URL", value=server_cfg["git_repo_url"]),
                k8s_client.V1EnvVar(name="GIT_BRANCH_OR_TAG", value=server_cfg["git_branch_or_tag"]),
                k8s_client.V1EnvVar(name="SERVER_FILE_PATH", value=server_cfg["server_file_path"]),
                k8s_client.V1EnvVar(name="MCP_INSTANCE_NAME", value=server_cfg["mcp_instance_name"]),
                k8s_client.V1EnvVar(name="SERVICE_PORT", value=str(server_cfg["service_port"]))
            ]
            
            # Add custom environment variables from server config
            if "env" in server_cfg and isinstance(server_cfg["env"], dict):
                for key, value in server_cfg["env"].items():
                    env_vars.append(k8s_client.V1EnvVar(name=key, value=str(value) if value is not None else ""))
            
            # Process secrets - create env vars from secrets
            volume_mounts = []
            volumes = []
            
            if "secrets" in server_cfg and isinstance(server_cfg["secrets"], list):
                for idx, secret_config in enumerate(server_cfg["secrets"]):
                    if isinstance(secret_config, dict) and "name" in secret_config:
                        secret_name = secret_config["name"]
                        # If mount_path is specified, mount the secret as a volume
                        if "mount_path" in secret_config and secret_config["mount_path"]:
                            mount_path = secret_config["mount_path"]
                            volume_name = f"secret-volume-{idx}"
                            
                            # Create volume mount
                            volume_mounts.append(
                                k8s_client.V1VolumeMount(
                                    name=volume_name,
                                    mount_path=mount_path,
                                    read_only=True
                                )
                            )
                            
                            # Create volume
                            volumes.append(
                                k8s_client.V1Volume(
                                    name=volume_name,
                                    secret=k8s_client.V1SecretVolumeSource(
                                        secret_name=secret_name
                                    )
                                )
                            )
                        else:
                            # Create environment variables from all keys in the secret
                            env_vars.append(
                                k8s_client.V1EnvFromSource(
                                    secret_ref=k8s_client.V1SecretEnvSource(
                                        name=secret_name
                                    )
                                )
                            )
                    elif isinstance(secret_config, str):
                        # Simple secret name, add as envFrom
                        env_vars.append(
                            k8s_client.V1EnvFromSource(
                                secret_ref=k8s_client.V1SecretEnvSource(
                                    name=secret_config
                                )
                            )
                        )
            
            # Add volume mounts from config
            if "volumes" in server_cfg and isinstance(server_cfg["volumes"], list):
                for vol in server_cfg["volumes"]:
                    if isinstance(vol, str) and ":" in vol:
                        # Format: "/host/path:/container/path[:ro]"
                        parts = vol.split(":")
                        if len(parts) >= 2:
                            host_path, container_path = parts[0], parts[1]
                            read_only = len(parts) > 2 and parts[2] == "ro"
                            
                            volume_name = f"hostpath-{len(volumes)}"
                            
                            # Create volume mount
                            volume_mounts.append(
                                k8s_client.V1VolumeMount(
                                    name=volume_name,
                                    mount_path=container_path,
                                    read_only=read_only
                                )
                            )
                            
                            # Create volume
                            volumes.append(
                                k8s_client.V1Volume(
                                    name=volume_name,
                                    host_path=k8s_client.V1HostPathVolumeSource(
                                        path=host_path
                                    )
                                )
                            )
            
            # Create container with all env vars, volume mounts, etc.
            container = k8s_client.V1Container(
                name=deployment_name,
                image=server_cfg["docker_image"],
                image_pull_policy="IfNotPresent",
                env=[var for var in env_vars if not hasattr(var, 'secret_ref')],
                env_from=[var for var in env_vars if hasattr(var, 'secret_ref')],
                ports=[k8s_client.V1ContainerPort(container_port=server_cfg["service_port"])],
                volume_mounts=volume_mounts if volume_mounts else None
            )
            template = k8s_client.V1PodTemplateSpec(
                metadata=k8s_client.V1ObjectMeta(labels={"app": deployment_name}),
                spec=k8s_client.V1PodSpec(
                    containers=[container],
                    volumes=volumes if volumes else None
                )
            )
            spec = k8s_client.V1DeploymentSpec(
                replicas=1,
                selector=k8s_client.V1LabelSelector(match_labels={"app": deployment_name}),
                template=template
            )
            deployment = k8s_client.V1Deployment(
                api_version="apps/v1",
                kind="Deployment",
                metadata=k8s_client.V1ObjectMeta(name=deployment_name, labels={"app": deployment_name}),
                spec=spec
            )
            apps_api.create_namespaced_deployment(namespace=namespace, body=deployment)
            logger.info("Deployment created successfully.")
        else:
            logger.error(f"Error checking Deployment existence: {api_exc}")
            return False

    # Ensure Service exists
    try:
        core_api.read_namespaced_service(name=service_name, namespace=namespace)
        logger.info(f"Service '{service_name}' already exists.")
    except k8s_client.exceptions.ApiException as api_exc:
        if api_exc.status == 404:
            logger.info(f"Creating Service '{service_name}'.")
            service_spec = k8s_client.V1ServiceSpec(
                selector={"app": deployment_name},
                ports=[k8s_client.V1ServicePort(port=server_cfg["service_port"], target_port=server_cfg["service_port"])],
                type="ClusterIP"
            )
            service = k8s_client.V1Service(
                api_version="v1",
                kind="Service",
                metadata=k8s_client.V1ObjectMeta(name=service_name),
                spec=service_spec
            )
            core_api.create_namespaced_service(namespace=namespace, body=service)
            logger.info("Service created successfully.")
        else:
            logger.error(f"Error checking Service existence: {api_exc}")
            return False

    return True

def main():
    logger.info("Starting MCP tool discovery and definition process...")

    # Optional: Check for Kubiya API Key if direct registration was needed
    # api_key = os.getenv("KUBIYA_API_KEY")
    # if not api_key:
    #     logger.error("KUBIYA_API_KEY environment variable is not set.")
    #     sys.exit(1) # Exit with error if key is required for the tool's purpose

    if not os.path.exists(CONFIG_FILE_PATH):
        logger.error(f"Configuration file not found inside the image at: {CONFIG_FILE_PATH}")
        sys.exit(1)

    # Perform discovery using the logic from discovery.py
    discovered_servers = discover_mcp_tools_from_config(CONFIG_FILE_PATH)

    tool_definitions = []
    if not discovered_servers:
        logger.warning("No MCP tools discovered. Check config and discovery logs.")
        # Output empty JSON array
        print(json.dumps([]))
        sys.exit(0)

    logger.info(f"Discovered {sum(len(s.tools) for s in discovered_servers)} potential tools from {len(discovered_servers)} servers.")

    # Generate Kubiya Tool definitions
    for server_info in discovered_servers:
        mode = server_info.config.get("mode", "sync").lower()
        if mode == "deploy":
            logger.info(f"Server '{server_info.config['id']}' is in 'deploy' mode. Ensuring Kubernetes deployment only.")
            if "docker_image" not in server_info.config:
                logger.error(f"'docker_image' is required for deploy mode on server {server_info.config['id']}. Skipping.")
                continue
            success = ensure_k8s_deployment(server_info.config)
            if success:
                logger.info(f"Deployment ensured for server {server_info.config['id']}.")
            continue  # Do not generate tool definitions for deploy-only servers

        # Default: sync mode (generate tool definitions)
        for tool_schema in server_info.tools:
            try:
                temp_tool_instance = ServerlessMCPTool(
                    mcp_server_config=server_info.config,
                    tool_schema=tool_schema.dict()
                )
                definition = temp_tool_instance.to_kubiya_definition_dict()
                tool_definitions.append(definition)
                logger.info(f"Generated definition for tool: {temp_tool_instance.name}")

            except Exception as e:
                logger.error(f"Failed to generate definition for MCP tool {tool_schema.name} from server {server_info.config.get('id')}: {e}", exc_info=True)

    # Output the JSON array of tool definitions to stdout
    logger.info(f"Outputting JSON definitions for {len(tool_definitions)} tools.")
    print(json.dumps(tool_definitions, indent=2))

if __name__ == "__main__":
    main() 