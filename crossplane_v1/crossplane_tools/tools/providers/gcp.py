"""GCP Provider Tools

This module provides tools for managing GCP resources through Crossplane.
"""
from typing import List, Dict, Any
from ..base import CrossplaneTool, Arg, Secret, get_provider_config
from kubiya_sdk.tools.registry import tool_registry
import sys
import logging

logger = logging.getLogger(__name__)

def create_gcp_resource_tool(resource_info: Dict[str, str], config: Dict[str, Any]) -> CrossplaneTool:
    """Create a tool for managing a specific GCP resource type."""
    name = resource_info['NAME'].replace('.gcp.crossplane.io', '')
    kind = resource_info['KIND']
    group = resource_info['GROUP']
    version = resource_info['VERSION']

    # Skip if resource is in exclude list
    if not config['sync_all'] and name not in config['include']:
        logger.info(f"Skipping {name} - not in include list")
        return None
    if name in config['exclude']:
        logger.info(f"Skipping {name} - in exclude list")
        return None

    return CrossplaneTool(
        name=f"gcp_{name.lower()}",
        description=f"Create and manage GCP {kind} using Crossplane",
        content=f"""
        if [ -z "$RESOURCE_NAME" ]; then
            echo "Error: Resource name not specified"
            exit 1
        fi

        # Get resource template
        TEMPLATE=$(generate_resource_template {resource_info['NAME']} $RESOURCE_NAME)

        # Create resource
        cat <<EOF | kubectl apply -f -
apiVersion: {group}/{version}
kind: {kind}
metadata:
  name: $RESOURCE_NAME
  ${{ANNOTATIONS:+annotations: $ANNOTATIONS}}
  ${{LABELS:+labels: $LABELS}}
spec:
  forProvider:
    project: $GOOGLE_PROJECT_ID
    ${{RESOURCE_CONFIG}}
  providerConfigRef:
    name: ${{PROVIDER_CONFIG:-default}}
EOF

        if [ "$WAIT" = "true" ]; then
            echo "Waiting for resource to be ready..."
            kubectl wait --for=condition=ready {name.lower()}.{group}/{version}/$RESOURCE_NAME --timeout=${{TIMEOUT:-300s}}
        fi

        if [ "$VERIFY" = "true" ]; then
            echo "\\nVerifying resource creation..."
            kubectl get {name.lower()}.{group}/{version} $RESOURCE_NAME -o yaml
        fi
        """,
        args=[
            Arg(name="resource_name", description=f"Name of the {kind} resource", required=True),
            Arg(name="resource_config", description="Resource-specific configuration in YAML format", required=True),
            Arg(name="provider_config", description="Name of the GCP provider configuration to use", required=False),
            Arg(name="wait", description="Wait for resource to be ready", required=False),
            Arg(name="verify", description="Verify resource creation", required=False),
            Arg(name="timeout", description="Timeout for waiting (default: 300s)", required=False)
        ],
        secrets=[Secret(**s) for s in config['secrets']],
        image="bitnami/kubectl:latest"
    )

def discover_gcp_resources() -> List[CrossplaneTool]:
    """Discover available GCP resource types and create corresponding tools."""
    tools = []
    
    # Get GCP provider configuration
    try:
        config = get_provider_config('gcp')
        if not config.get('enabled', True):
            logger.info("GCP provider is disabled in configuration")
            return tools
    except Exception as e:
        logger.error(f"Failed to get GCP provider configuration: {str(e)}")
        return tools

    # Add core GCP tools if they match configuration
    core_tools = {
        'gke': gcp_gke_cluster_tool,
        'storage': gcp_storage_bucket_tool,
        'sql': gcp_sql_instance_tool,
        'vpc': gcp_vpc_network_tool
    }

    for name, tool in core_tools.items():
        if config['sync_all'] or name in config['include']:
            if name not in config['exclude']:
                tool.secrets = [Secret(**s) for s in config['secrets']]
                tools.append(tool)
                logger.info(f"Added core tool: {name}")

    try:
        # Discover additional GCP resources
        logger.info("Discovering GCP provider resources...")
        resource_list = """
        discover_provider_resources gcp | while read -r resource; do
            echo "$resource"
        done
        """
        
        # Create tools for discovered resources
        for resource_info in resource_list.split('\n'):
            if resource_info.strip():
                try:
                    parts = resource_info.split()
                    if len(parts) == 4:
                        resource_data = {
                            'NAME': parts[0],
                            'GROUP': parts[1],
                            'VERSION': parts[2],
                            'KIND': parts[3]
                        }
                        # Skip resources that already have dedicated tools
                        if not any(t.name == f"gcp_{resource_data['NAME'].lower()}" for t in tools):
                            tool = create_gcp_resource_tool(resource_data, config)
                            if tool:
                                tools.append(tool)
                                logger.info(f"✅ Created tool for: {resource_data['KIND']}")
                except Exception as e:
                    logger.error(f"❌ Failed to create tool for resource: {resource_info} - {str(e)}")
    except Exception as e:
        logger.error(f"❌ Failed to discover GCP resources: {str(e)}")

    return tools

# Core GCP tools with secrets
gcp_gke_cluster_tool = CrossplaneTool(
    name="gcp_gke_cluster",
    description="Create and manage GCP GKE clusters using Crossplane",
    content="""
    if [ -z "$CLUSTER_NAME" ]; then
        echo "Error: Cluster name not specified"
        exit 1
    fi

    # Create GKE cluster resource
    cat <<EOF | kubectl apply -f -
apiVersion: container.gcp.crossplane.io/v1beta1
kind: Cluster
metadata:
  name: ${CLUSTER_NAME}
  ${ANNOTATIONS:+annotations: $ANNOTATIONS}
  ${LABELS:+labels: $LABELS}
spec:
  forProvider:
    project: $GOOGLE_PROJECT_ID
    location: ${LOCATION:-us-central1-a}
    initialClusterVersion: ${VERSION:-1.27}
    network: ${NETWORK:-default}
    subnetwork: ${SUBNETWORK:-default}
    ipAllocationPolicy:
      useIpAliases: true
    masterAuth:
      clientCertificateConfig:
        issueClientCertificate: false
    ${PRIVATE_CLUSTER:+privateClusterConfig: $PRIVATE_CLUSTER}
    ${NODE_POOLS:+nodePools: $NODE_POOLS}
    ${LOGGING_SERVICE:+loggingService: $LOGGING_SERVICE}
    ${MONITORING_SERVICE:+monitoringService: $MONITORING_SERVICE}
    ${ADDONS_CONFIG:+addonsConfig: $ADDONS_CONFIG}
    ${NETWORK_POLICY:+networkPolicy: $NETWORK_POLICY}
    ${MAINTENANCE_POLICY:+maintenancePolicy: $MAINTENANCE_POLICY}
    ${RESOURCE_LABELS:+resourceLabels: $RESOURCE_LABELS}
  providerConfigRef:
    name: ${PROVIDER_CONFIG:-default}
EOF

    if [ "$WAIT" = "true" ]; then
        echo "Waiting for cluster to be ready..."
        kubectl wait --for=condition=ready cluster.container.gcp.crossplane.io/${CLUSTER_NAME} --timeout=${TIMEOUT:-900s}
    fi

    if [ "$VERIFY" = "true" ]; then
        echo "\\nVerifying cluster creation..."
        kubectl get cluster.container.gcp.crossplane.io ${CLUSTER_NAME} -o yaml
    fi
    """,
    args=[
        Arg(name="cluster_name", description="Name of the GKE cluster", required=True),
        Arg(name="location", description="GCP zone or region for the cluster", required=False),
        Arg(name="version", description="Kubernetes version for the cluster", required=False),
        Arg(name="network", description="VPC network name", required=False),
        Arg(name="subnetwork", description="VPC subnetwork name", required=False),
        Arg(name="private_cluster", description="Private cluster configuration", required=False),
        Arg(name="node_pools", description="Node pool configurations", required=False),
        Arg(name="logging_service", description="Logging service configuration", required=False),
        Arg(name="monitoring_service", description="Monitoring service configuration", required=False),
        Arg(name="addons_config", description="Cluster addons configuration", required=False),
        Arg(name="network_policy", description="Network policy configuration", required=False),
        Arg(name="maintenance_policy", description="Maintenance window configuration", required=False),
        Arg(name="resource_labels", description="Labels to apply to the cluster", required=False),
        Arg(name="provider_config", description="Name of the GCP provider configuration to use", required=False),
        Arg(name="wait", description="Wait for cluster to be ready", required=False),
        Arg(name="verify", description="Verify cluster creation", required=False),
        Arg(name="timeout", description="Timeout for waiting (default: 900s)", required=False)
    ],
    image="bitnami/kubectl:latest"
)

# GCP Storage Bucket Tool
gcp_storage_bucket_tool = CrossplaneTool(
    name="gcp_storage_bucket",
    description="Create and manage GCP Storage buckets using Crossplane",
    content="""
    if [ -z "$BUCKET_NAME" ]; then
        echo "Error: Bucket name not specified"
        exit 1
    fi

    # Create Storage bucket resource
    cat <<EOF | kubectl apply -f -
apiVersion: storage.gcp.crossplane.io/v1alpha3
kind: Bucket
metadata:
  name: ${BUCKET_NAME}
  ${ANNOTATIONS:+annotations: $ANNOTATIONS}
  ${LABELS:+labels: $LABELS}
spec:
  forProvider:
    location: ${LOCATION:-US}
    storageClass: ${STORAGE_CLASS:-STANDARD}
    uniformBucketLevelAccess: ${UNIFORM_ACCESS:-true}
    versioning:
      enabled: ${VERSIONING:-false}
    ${LIFECYCLE_RULES:+lifecycleRules: $LIFECYCLE_RULES}
    ${CORS:+cors: $CORS}
    ${ENCRYPTION:+encryption: $ENCRYPTION}
    ${LABELS:+labels: $LABELS}
  providerConfigRef:
    name: ${PROVIDER_CONFIG:-default}
EOF

    if [ "$WAIT" = "true" ]; then
        echo "Waiting for bucket to be ready..."
        kubectl wait --for=condition=ready bucket.storage.gcp.crossplane.io/${BUCKET_NAME} --timeout=${TIMEOUT:-300s}
    fi

    if [ "$VERIFY" = "true" ]; then
        echo "\\nVerifying bucket creation..."
        kubectl get bucket.storage.gcp.crossplane.io ${BUCKET_NAME} -o yaml
    fi
    """,
    args=[
        Arg(name="bucket_name", description="Name of the Storage bucket", required=True),
        Arg(name="location", description="Location for the bucket", required=False),
        Arg(name="storage_class", description="Storage class for the bucket", required=False),
        Arg(name="uniform_access", description="Enable uniform bucket-level access", required=False),
        Arg(name="versioning", description="Enable object versioning", required=False),
        Arg(name="lifecycle_rules", description="Lifecycle management rules", required=False),
        Arg(name="cors", description="CORS configuration", required=False),
        Arg(name="encryption", description="Encryption configuration", required=False),
        Arg(name="labels", description="Labels to apply to the bucket", required=False),
        Arg(name="provider_config", description="Name of the GCP provider configuration to use", required=False),
        Arg(name="wait", description="Wait for bucket to be ready", required=False),
        Arg(name="verify", description="Verify bucket creation", required=False),
        Arg(name="timeout", description="Timeout for waiting (default: 300s)", required=False)
    ],
    image="bitnami/kubectl:latest"
)

# GCP SQL Instance Tool
gcp_sql_instance_tool = CrossplaneTool(
    name="gcp_sql_instance",
    description="Create and manage GCP Cloud SQL instances using Crossplane",
    content="""
    if [ -z "$INSTANCE_NAME" ]; then
        echo "Error: Instance name not specified"
        exit 1
    fi

    # Create Cloud SQL instance resource
    cat <<EOF | kubectl apply -f -
apiVersion: database.gcp.crossplane.io/v1beta1
kind: CloudSQLInstance
metadata:
  name: ${INSTANCE_NAME}
  ${ANNOTATIONS:+annotations: $ANNOTATIONS}
  ${LABELS:+labels: $LABELS}
spec:
  forProvider:
    databaseVersion: ${DATABASE_VERSION:-POSTGRES_13}
    region: ${REGION:-us-central1}
    settings:
      tier: ${TIER:-db-f1-micro}
      dataDiskSizeGb: ${DISK_SIZE:-10}
      dataDiskType: ${DISK_TYPE:-PD_SSD}
      ipConfiguration:
        ipv4Enabled: ${IPV4_ENABLED:-true}
        requireSsl: ${REQUIRE_SSL:-true}
        ${AUTHORIZED_NETWORKS:+authorizedNetworks: $AUTHORIZED_NETWORKS}
      ${BACKUP_CONFIG:+backupConfiguration: $BACKUP_CONFIG}
      ${DATABASE_FLAGS:+databaseFlags: $DATABASE_FLAGS}
      ${MAINTENANCE_WINDOW:+maintenanceWindow: $MAINTENANCE_WINDOW}
      ${USER_LABELS:+userLabels: $USER_LABELS}
  providerConfigRef:
    name: ${PROVIDER_CONFIG:-default}
EOF

    if [ "$WAIT" = "true" ]; then
        echo "Waiting for SQL instance to be ready..."
        kubectl wait --for=condition=ready cloudsqlinstance.database.gcp.crossplane.io/${INSTANCE_NAME} --timeout=${TIMEOUT:-900s}
    fi

    if [ "$VERIFY" = "true" ]; then
        echo "\\nVerifying SQL instance creation..."
        kubectl get cloudsqlinstance.database.gcp.crossplane.io ${INSTANCE_NAME} -o yaml
    fi
    """,
    args=[
        Arg(name="instance_name", description="Name of the Cloud SQL instance", required=True),
        Arg(name="database_version", description="Database version (e.g., POSTGRES_13)", required=False),
        Arg(name="region", description="Region for the instance", required=False),
        Arg(name="tier", description="Machine type for the instance", required=False),
        Arg(name="disk_size", description="Data disk size in GB", required=False),
        Arg(name="disk_type", description="Data disk type", required=False),
        Arg(name="ipv4_enabled", description="Enable IPv4 access", required=False),
        Arg(name="require_ssl", description="Require SSL connections", required=False),
        Arg(name="authorized_networks", description="Authorized networks configuration", required=False),
        Arg(name="backup_config", description="Backup configuration", required=False),
        Arg(name="database_flags", description="Database flags configuration", required=False),
        Arg(name="maintenance_window", description="Maintenance window configuration", required=False),
        Arg(name="user_labels", description="Labels to apply to the instance", required=False),
        Arg(name="provider_config", description="Name of the GCP provider configuration to use", required=False),
        Arg(name="wait", description="Wait for instance to be ready", required=False),
        Arg(name="verify", description="Verify instance creation", required=False),
        Arg(name="timeout", description="Timeout for waiting (default: 900s)", required=False)
    ],
    image="bitnami/kubectl:latest"
)

# GCP VPC Network Tool
gcp_vpc_network_tool = CrossplaneTool(
    name="gcp_vpc_network",
    description="Create and manage GCP VPC networks using Crossplane",
    content="""
    if [ -z "$NETWORK_NAME" ]; then
        echo "Error: Network name not specified"
        exit 1
    fi

    # Create VPC network resource
    cat <<EOF | kubectl apply -f -
apiVersion: compute.gcp.crossplane.io/v1beta1
kind: Network
metadata:
  name: ${NETWORK_NAME}
  ${ANNOTATIONS:+annotations: $ANNOTATIONS}
  ${LABELS:+labels: $LABELS}
spec:
  forProvider:
    autoCreateSubnetworks: ${AUTO_SUBNETS:-false}
    routingMode: ${ROUTING_MODE:-REGIONAL}
    ${DESCRIPTION:+description: $DESCRIPTION}
    ${MTU:+mtu: $MTU}
    ${NETWORK_FIREWALL_POLICY:+networkFirewallPolicyEnforcementOrder: $NETWORK_FIREWALL_POLICY}
  providerConfigRef:
    name: ${PROVIDER_CONFIG:-default}
EOF

    if [ "$WAIT" = "true" ]; then
        echo "Waiting for network to be ready..."
        kubectl wait --for=condition=ready network.compute.gcp.crossplane.io/${NETWORK_NAME} --timeout=${TIMEOUT:-300s}
    fi

    if [ "$VERIFY" = "true" ]; then
        echo "\\nVerifying network creation..."
        kubectl get network.compute.gcp.crossplane.io ${NETWORK_NAME} -o yaml
    fi
    """,
    args=[
        Arg(name="network_name", description="Name of the VPC network", required=True),
        Arg(name="auto_subnets", description="Auto-create subnetworks", required=False),
        Arg(name="routing_mode", description="Network-wide routing mode", required=False),
        Arg(name="description", description="Network description", required=False),
        Arg(name="mtu", description="Maximum Transmission Unit in bytes", required=False),
        Arg(name="network_firewall_policy", description="Network firewall policy enforcement order", required=False),
        Arg(name="provider_config", description="Name of the GCP provider configuration to use", required=False),
        Arg(name="wait", description="Wait for network to be ready", required=False),
        Arg(name="verify", description="Verify network creation", required=False),
        Arg(name="timeout", description="Timeout for waiting (default: 300s)", required=False)
    ],
    image="bitnami/kubectl:latest"
)

# Register GCP tools
try:
    logger.info("=== Registering GCP Provider Tools ===")
    gcp_tools = discover_gcp_resources()
    
    for tool in gcp_tools:
        try:
            tool_registry.register("crossplane", tool)
            logger.info(f"✅ Registered: {tool.name}")
        except Exception as e:
            logger.error(f"❌ Failed to register {tool.name}: {str(e)}")
except Exception as e:
    logger.error(f"❌ Failed to register GCP tools: {str(e)}")

# Export tools
__all__ = [
    'gcp_gke_cluster_tool',
    'gcp_storage_bucket_tool',
    'gcp_sql_instance_tool',
    'gcp_vpc_network_tool',
    'discover_gcp_resources'
] 