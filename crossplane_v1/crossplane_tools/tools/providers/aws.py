"""AWS Provider Tools

This module provides tools for managing AWS resources through Crossplane.
"""
from typing import List, Dict, Any
from ..base import CrossplaneTool, Arg, Secret, get_provider_config
from kubiya_sdk.tools.registry import tool_registry
import sys
import logging

logger = logging.getLogger(__name__)

def create_aws_resource_tool(resource_info: Dict[str, str], config: Dict[str, Any]) -> CrossplaneTool:
    """Create a tool for managing a specific AWS resource type."""
    name = resource_info['NAME'].replace('.aws.crossplane.io', '')
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
        name=f"aws_{name.lower()}",
        description=f"Create and manage AWS {kind} using Crossplane",
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
    region: ${{REGION:-$AWS_REGION}}
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
            Arg(name="region", description="AWS region for the resource", required=False),
            Arg(name="provider_config", description="Name of the AWS provider configuration to use", required=False),
            Arg(name="wait", description="Wait for resource to be ready", required=False),
            Arg(name="verify", description="Verify resource creation", required=False),
            Arg(name="timeout", description="Timeout for waiting (default: 300s)", required=False)
        ],
        secrets=[Secret(**s) for s in config['secrets']],
        image="bitnami/kubectl:latest"
    )

def discover_aws_resources() -> List[CrossplaneTool]:
    """Discover available AWS resource types and create corresponding tools."""
    tools = []
    
    # Get AWS provider configuration
    try:
        config = get_provider_config('aws')
        if not config.get('enabled', True):
            logger.info("AWS provider is disabled in configuration")
            return tools
    except Exception as e:
        logger.error(f"Failed to get AWS provider configuration: {str(e)}")
        return tools

    # Add core AWS tools if they match configuration
    core_tools = {
        's3': aws_s3_bucket_tool,
        'eks': aws_eks_cluster_tool,
        'rds': aws_rds_instance_tool,
        'vpc': aws_vpc_tool
    }

    for name, tool in core_tools.items():
        if config['sync_all'] or name in config['include']:
            if name not in config['exclude']:
                tool.secrets = [Secret(**s) for s in config['secrets']]
                tools.append(tool)
                logger.info(f"Added core tool: {name}")

    try:
        # Discover additional AWS resources
        logger.info("Discovering AWS provider resources...")
        resource_list = """
        discover_provider_resources aws | while read -r resource; do
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
                        if not any(t.name == f"aws_{resource_data['NAME'].lower()}" for t in tools):
                            tool = create_aws_resource_tool(resource_data, config)
                            if tool:
                                tools.append(tool)
                                logger.info(f"✅ Created tool for: {resource_data['KIND']}")
                except Exception as e:
                    logger.error(f"❌ Failed to create tool for resource: {resource_info} - {str(e)}")
    except Exception as e:
        logger.error(f"❌ Failed to discover AWS resources: {str(e)}")

    return tools

# Core AWS tools with secrets
aws_s3_bucket_tool = CrossplaneTool(
    name="aws_s3_bucket",
    description="Create and manage AWS S3 buckets using Crossplane",
    content="""
    if [ -z "$BUCKET_NAME" ]; then
        echo "Error: Bucket name not specified"
        exit 1
    fi

    # Create S3 bucket resource
    cat <<EOF | kubectl apply -f -
apiVersion: s3.aws.crossplane.io/v1beta1
kind: Bucket
metadata:
  name: ${BUCKET_NAME}
  ${ANNOTATIONS:+annotations: $ANNOTATIONS}
  ${LABELS:+labels: $LABELS}
spec:
  forProvider:
    region: ${REGION:-$AWS_REGION}
    acl: ${ACL:-private}
    locationConstraint: ${REGION:-$AWS_REGION}
    ${VERSIONING:+versioning: $VERSIONING}
    ${PUBLIC_ACCESS_BLOCK:+publicAccessBlock: $PUBLIC_ACCESS_BLOCK}
    ${ENCRYPTION:+serverSideEncryptionConfiguration: $ENCRYPTION}
    ${LIFECYCLE_RULES:+lifecycleRules: $LIFECYCLE_RULES}
    ${TAGS:+tags: $TAGS}
  providerConfigRef:
    name: ${PROVIDER_CONFIG:-default}
EOF

    if [ "$WAIT" = "true" ]; then
        echo "Waiting for bucket to be ready..."
        kubectl wait --for=condition=ready bucket.s3.aws.crossplane.io/${BUCKET_NAME} --timeout=${TIMEOUT:-300s}
    fi

    if [ "$VERIFY" = "true" ]; then
        echo "\\nVerifying bucket creation..."
        kubectl get bucket.s3.aws.crossplane.io ${BUCKET_NAME} -o yaml
    fi
    """,
    args=[
        Arg(name="bucket_name", description="Name of the S3 bucket to create", required=True),
        Arg(name="acl", description="Access control list for the bucket", required=False),
        Arg(name="versioning", description="Enable versioning for the bucket", required=False),
        Arg(name="public_access_block", description="Block public access configuration", required=False),
        Arg(name="encryption", description="Server-side encryption configuration", required=False),
        Arg(name="lifecycle_rules", description="Lifecycle rules for the bucket", required=False),
        Arg(name="tags", description="Tags to apply to the bucket", required=False),
        Arg(name="provider_config", description="Name of the AWS provider configuration to use", required=False),
        Arg(name="wait", description="Wait for bucket to be ready", required=False),
        Arg(name="verify", description="Verify bucket creation", required=False),
        Arg(name="timeout", description="Timeout for waiting (default: 300s)", required=False)
    ],
    image="bitnami/kubectl:latest"
)

# AWS EKS Cluster Tool
aws_eks_cluster_tool = CrossplaneTool(
    name="aws_eks_cluster",
    description="Create and manage AWS EKS clusters using Crossplane",
    content="""
    if [ -z "$CLUSTER_NAME" ]; then
        echo "Error: Cluster name not specified"
        exit 1
    fi

    # Create EKS cluster resource
    cat <<EOF | kubectl apply -f -
apiVersion: eks.aws.crossplane.io/v1beta1
kind: Cluster
metadata:
  name: ${CLUSTER_NAME}
  ${ANNOTATIONS:+annotations: $ANNOTATIONS}
  ${LABELS:+labels: $LABELS}
spec:
  forProvider:
    region: ${REGION:-us-west-2}
    version: ${VERSION:-1.27}
    roleArnRef:
      name: ${ROLE_NAME:-eks-cluster-role}
    resourcesVpcConfig:
      subnetIds: ${SUBNET_IDS}
      ${SECURITY_GROUP_IDS:+securityGroupIds: $SECURITY_GROUP_IDS}
      endpointPrivateAccess: ${PRIVATE_ACCESS:-false}
      endpointPublicAccess: ${PUBLIC_ACCESS:-true}
    ${ENCRYPTION_CONFIG:+encryptionConfig: $ENCRYPTION_CONFIG}
    ${LOGGING:+logging: $LOGGING}
    ${TAGS:+tags: $TAGS}
  providerConfigRef:
    name: ${PROVIDER_CONFIG:-default}
EOF

    if [ "$WAIT" = "true" ]; then
        echo "Waiting for cluster to be ready..."
        kubectl wait --for=condition=ready cluster.eks.aws.crossplane.io/${CLUSTER_NAME} --timeout=${TIMEOUT:-900s}
    fi

    if [ "$VERIFY" = "true" ]; then
        echo "\\nVerifying cluster creation..."
        kubectl get cluster.eks.aws.crossplane.io ${CLUSTER_NAME} -o yaml
    fi
    """,
    args=[
        Arg(name="cluster_name", description="Name of the EKS cluster", required=True),
        Arg(name="region", description="AWS region for the cluster", required=False),
        Arg(name="version", description="Kubernetes version for the cluster", required=False),
        Arg(name="role_name", description="Name of the IAM role for the cluster", required=False),
        Arg(name="subnet_ids", description="List of subnet IDs for the cluster VPC", required=True),
        Arg(name="security_group_ids", description="List of security group IDs", required=False),
        Arg(name="private_access", description="Enable private API endpoint access", required=False),
        Arg(name="public_access", description="Enable public API endpoint access", required=False),
        Arg(name="encryption_config", description="KMS encryption configuration", required=False),
        Arg(name="logging", description="Control plane logging configuration", required=False),
        Arg(name="tags", description="Tags to apply to the cluster", required=False),
        Arg(name="provider_config", description="Name of the AWS provider configuration to use", required=False),
        Arg(name="wait", description="Wait for cluster to be ready", required=False),
        Arg(name="verify", description="Verify cluster creation", required=False),
        Arg(name="timeout", description="Timeout for waiting (default: 900s)", required=False)
    ],
    image="bitnami/kubectl:latest"
)

# AWS RDS Instance Tool
aws_rds_instance_tool = CrossplaneTool(
    name="aws_rds_instance",
    description="Create and manage AWS RDS instances using Crossplane",
    content="""
    if [ -z "$INSTANCE_NAME" ]; then
        echo "Error: Instance name not specified"
        exit 1
    fi

    # Create RDS instance resource
    cat <<EOF | kubectl apply -f -
apiVersion: database.aws.crossplane.io/v1beta1
kind: RDSInstance
metadata:
  name: ${INSTANCE_NAME}
  ${ANNOTATIONS:+annotations: $ANNOTATIONS}
  ${LABELS:+labels: $LABELS}
spec:
  forProvider:
    region: ${REGION:-us-west-2}
    dbInstanceClass: ${INSTANCE_CLASS:-db.t3.micro}
    engine: ${ENGINE:-postgres}
    engineVersion: ${ENGINE_VERSION:-13.7}
    masterUsername: ${MASTER_USERNAME:-admin}
    masterPasswordSecretRef:
      name: ${PASSWORD_SECRET:-rds-password}
      key: ${PASSWORD_KEY:-password}
    allocatedStorage: ${STORAGE_SIZE:-20}
    publiclyAccessible: ${PUBLIC_ACCESS:-false}
    ${SUBNET_GROUP:+dbSubnetGroupName: $SUBNET_GROUP}
    ${SECURITY_GROUPS:+vpcSecurityGroupIds: $SECURITY_GROUPS}
    ${BACKUP_RETENTION:+backupRetentionPeriod: $BACKUP_RETENTION}
    ${MULTI_AZ:+multiAZ: $MULTI_AZ}
    ${STORAGE_TYPE:+storageType: $STORAGE_TYPE}
    ${TAGS:+tags: $TAGS}
  providerConfigRef:
    name: ${PROVIDER_CONFIG:-default}
EOF

    if [ "$WAIT" = "true" ]; then
        echo "Waiting for RDS instance to be ready..."
        kubectl wait --for=condition=ready rdsinstance.database.aws.crossplane.io/${INSTANCE_NAME} --timeout=${TIMEOUT:-900s}
    fi

    if [ "$VERIFY" = "true" ]; then
        echo "\\nVerifying RDS instance creation..."
        kubectl get rdsinstance.database.aws.crossplane.io ${INSTANCE_NAME} -o yaml
    fi
    """,
    args=[
        Arg(name="instance_name", description="Name of the RDS instance", required=True),
        Arg(name="region", description="AWS region for the instance", required=False),
        Arg(name="instance_class", description="DB instance class", required=False),
        Arg(name="engine", description="Database engine (mysql, postgres, etc.)", required=False),
        Arg(name="engine_version", description="Database engine version", required=False),
        Arg(name="master_username", description="Master user username", required=False),
        Arg(name="password_secret", description="Name of the secret containing the master password", required=False),
        Arg(name="password_key", description="Key in the secret containing the password", required=False),
        Arg(name="storage_size", description="Allocated storage in GB", required=False),
        Arg(name="public_access", description="Make instance publicly accessible", required=False),
        Arg(name="subnet_group", description="DB subnet group name", required=False),
        Arg(name="security_groups", description="VPC security group IDs", required=False),
        Arg(name="backup_retention", description="Backup retention period in days", required=False),
        Arg(name="multi_az", description="Enable Multi-AZ deployment", required=False),
        Arg(name="storage_type", description="Storage type (gp2, io1, etc.)", required=False),
        Arg(name="tags", description="Tags to apply to the instance", required=False),
        Arg(name="provider_config", description="Name of the AWS provider configuration to use", required=False),
        Arg(name="wait", description="Wait for instance to be ready", required=False),
        Arg(name="verify", description="Verify instance creation", required=False),
        Arg(name="timeout", description="Timeout for waiting (default: 900s)", required=False)
    ],
    image="bitnami/kubectl:latest"
)

# AWS VPC Tool
aws_vpc_tool = CrossplaneTool(
    name="aws_vpc",
    description="Create and manage AWS VPCs using Crossplane",
    content="""
    if [ -z "$VPC_NAME" ]; then
        echo "Error: VPC name not specified"
        exit 1
    fi

    # Create VPC resource
    cat <<EOF | kubectl apply -f -
apiVersion: ec2.aws.crossplane.io/v1beta1
kind: VPC
metadata:
  name: ${VPC_NAME}
  ${ANNOTATIONS:+annotations: $ANNOTATIONS}
  ${LABELS:+labels: $LABELS}
spec:
  forProvider:
    region: ${REGION:-us-west-2}
    cidrBlock: ${CIDR_BLOCK:-10.0.0.0/16}
    enableDnsHostnames: ${DNS_HOSTNAMES:-true}
    enableDnsSupport: ${DNS_SUPPORT:-true}
    ${INSTANCE_TENANCY:+instanceTenancy: $INSTANCE_TENANCY}
    ${TAGS:+tags: $TAGS}
  providerConfigRef:
    name: ${PROVIDER_CONFIG:-default}
EOF

    if [ "$WAIT" = "true" ]; then
        echo "Waiting for VPC to be ready..."
        kubectl wait --for=condition=ready vpc.ec2.aws.crossplane.io/${VPC_NAME} --timeout=${TIMEOUT:-300s}
    fi

    if [ "$VERIFY" = "true" ]; then
        echo "\\nVerifying VPC creation..."
        kubectl get vpc.ec2.aws.crossplane.io ${VPC_NAME} -o yaml
    fi
    """,
    args=[
        Arg(name="vpc_name", description="Name of the VPC", required=True),
        Arg(name="region", description="AWS region for the VPC", required=False),
        Arg(name="cidr_block", description="CIDR block for the VPC", required=False),
        Arg(name="dns_hostnames", description="Enable DNS hostnames", required=False),
        Arg(name="dns_support", description="Enable DNS support", required=False),
        Arg(name="instance_tenancy", description="Instance tenancy (default, dedicated)", required=False),
        Arg(name="tags", description="Tags to apply to the VPC", required=False),
        Arg(name="provider_config", description="Name of the AWS provider configuration to use", required=False),
        Arg(name="wait", description="Wait for VPC to be ready", required=False),
        Arg(name="verify", description="Verify VPC creation", required=False),
        Arg(name="timeout", description="Timeout for waiting (default: 300s)", required=False)
    ],
    image="bitnami/kubectl:latest"
)

# Register AWS tools
try:
    logger.info("=== Registering AWS Provider Tools ===")
    aws_tools = discover_aws_resources()
    
    for tool in aws_tools:
        try:
            tool_registry.register("crossplane", tool)
            logger.info(f"✅ Registered: {tool.name}")
        except Exception as e:
            logger.error(f"❌ Failed to register {tool.name}: {str(e)}")
except Exception as e:
    logger.error(f"❌ Failed to register AWS tools: {str(e)}")

# Export tools
__all__ = [
    'aws_s3_bucket_tool',
    'aws_eks_cluster_tool',
    'aws_rds_instance_tool',
    'aws_vpc_tool',
    'discover_aws_resources'
] 