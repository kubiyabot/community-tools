from typing import List
from ..base import CrossplaneTool, Arg

class AWSProviderManager(CrossplaneTool):
    """Manage AWS-specific Crossplane provider operations."""
    
    def __init__(self):
        super().__init__(
            name="aws_provider",
            description="Manage AWS provider and resources",
            content="",
            args=[],
            image="bitnami/kubectl:latest",
            mermaid="""
```mermaid
classDiagram
    class CrossplaneTool {
        <<base>>
    }
    class AWSProviderManager {
        +install_provider()
        +configure_credentials()
        +create_eks_cluster()
        +create_rds_instance()
        +create_s3_bucket()
        +create_vpc()
        +list_resources()
    }
    CrossplaneTool <|-- AWSProviderManager
    note for AWSProviderManager "Manages AWS-specific\nresources and configurations"
```
"""
        )

    def install_provider(self) -> CrossplaneTool:
        """Install AWS provider."""
        return CrossplaneTool(
            name="install_aws_provider",
            description="Install AWS provider and its CRDs",
            content="""
            # Install AWS provider
            cat <<EOF | kubectl apply -f -
apiVersion: pkg.crossplane.io/v1
kind: Provider
metadata:
  name: provider-aws
spec:
  package: xpkg.upbound.io/upbound/provider-aws:v0.37.0
EOF

            # Wait for provider to be healthy
            kubectl wait --for=condition=healthy provider.pkg.crossplane.io/provider-aws --timeout=300s
            """,
            args=[],
            image="bitnami/kubectl:latest"
        )

    def configure_credentials(self) -> CrossplaneTool:
        """Configure AWS credentials."""
        return CrossplaneTool(
            name="configure_aws_credentials",
            description="Configure AWS provider credentials",
            content="""
            if [ -z "$AWS_ACCESS_KEY_ID" ] || [ -z "$AWS_SECRET_ACCESS_KEY" ]; then
                echo "Error: AWS credentials not specified"
                exit 1
            fi

            # Create AWS credentials secret
            cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Secret
metadata:
  name: aws-creds
  namespace: crossplane-system
type: Opaque
stringData:
  credentials: |
    [default]
    aws_access_key_id = ${AWS_ACCESS_KEY_ID}
    aws_secret_access_key = ${AWS_SECRET_ACCESS_KEY}
EOF

            # Create ProviderConfig
            cat <<EOF | kubectl apply -f -
apiVersion: aws.crossplane.io/v1beta1
kind: ProviderConfig
metadata:
  name: default
spec:
  credentials:
    source: Secret
    secretRef:
      namespace: crossplane-system
      name: aws-creds
      key: credentials
  region: ${AWS_REGION:-us-west-2}
EOF
            """,
            args=[
                Arg("aws_access_key_id",
                    description="AWS Access Key ID",
                    required=True),
                Arg("aws_secret_access_key",
                    description="AWS Secret Access Key",
                    required=True),
                Arg("aws_region",
                    description="AWS region (defaults to us-west-2)",
                    required=False)
            ],
            image="bitnami/kubectl:latest"
        )

    def create_eks_cluster(self) -> CrossplaneTool:
        """Create an EKS cluster."""
        return CrossplaneTool(
            name="create_eks_cluster",
            description="Create an AWS EKS cluster",
            content="""
            if [ -z "$CLUSTER_NAME" ]; then
                echo "Error: Cluster name not specified"
                exit 1
            fi

            cat <<EOF | kubectl apply -f -
apiVersion: eks.aws.crossplane.io/v1beta1
kind: Cluster
metadata:
  name: $CLUSTER_NAME
spec:
  forProvider:
    region: ${REGION:-us-west-2}
    version: ${VERSION:-1.27}
    roleArnRef:
      name: eks-cluster-role
    resourcesVpcConfig:
      subnetIds: ${SUBNET_IDS:-[]}
      endpointPrivateAccess: true
      endpointPublicAccess: true
  providerConfigRef:
    name: default
EOF

            # Wait for cluster to be ready
            kubectl wait --for=condition=ready cluster.eks.aws.crossplane.io/$CLUSTER_NAME --timeout=900s
            """,
            args=[
                Arg("cluster_name",
                    description="Name of the EKS cluster",
                    required=True),
                Arg("region",
                    description="AWS region (defaults to us-west-2)",
                    required=False),
                Arg("version",
                    description="Kubernetes version (defaults to 1.27)",
                    required=False),
                Arg("subnet_ids",
                    description="List of subnet IDs for the cluster",
                    required=False)
            ],
            image="bitnami/kubectl:latest"
        )

    def create_s3_bucket(self) -> CrossplaneTool:
        """Create an S3 bucket."""
        return CrossplaneTool(
            name="create_s3_bucket",
            description="Create an AWS S3 bucket",
            content="""
            if [ -z "$BUCKET_NAME" ]; then
                echo "Error: Bucket name not specified"
                exit 1
            fi

            cat <<EOF | kubectl apply -f -
apiVersion: s3.aws.crossplane.io/v1beta1
kind: Bucket
metadata:
  name: $BUCKET_NAME
spec:
  forProvider:
    locationConstraint: ${REGION:-us-west-2}
    acl: ${ACL:-private}
    versioning: true
    publicAccessBlockConfiguration:
      blockPublicAcls: true
      blockPublicPolicy: true
      ignorePublicAcls: true
      restrictPublicBuckets: true
    serverSideEncryptionConfiguration:
      rules:
        - applyServerSideEncryptionByDefault:
            sseAlgorithm: AES256
  providerConfigRef:
    name: default
EOF

            # Wait for bucket to be ready
            kubectl wait --for=condition=ready bucket.s3.aws.crossplane.io/$BUCKET_NAME --timeout=300s
            """,
            args=[
                Arg("bucket_name",
                    description="Name of the S3 bucket",
                    required=True),
                Arg("region",
                    description="AWS region (defaults to us-west-2)",
                    required=False),
                Arg("acl",
                    description="Bucket ACL (defaults to private)",
                    required=False)
            ],
            image="bitnami/kubectl:latest"
        )

    def create_rds_instance(self) -> CrossplaneTool:
        """Create an RDS instance."""
        return CrossplaneTool(
            name="create_rds_instance",
            description="Create an AWS RDS instance",
            content="""
            if [ -z "$INSTANCE_NAME" ] || [ -z "$DB_NAME" ]; then
                echo "Error: Instance name and database name are required"
                exit 1
            fi

            cat <<EOF | kubectl apply -f -
apiVersion: rds.aws.crossplane.io/v1beta1
kind: Instance
metadata:
  name: $INSTANCE_NAME
spec:
  forProvider:
    region: ${REGION:-us-west-2}
    dbName: $DB_NAME
    engine: ${ENGINE:-postgres}
    engineVersion: ${ENGINE_VERSION:-14.7}
    dbInstanceClass: ${INSTANCE_CLASS:-db.t3.micro}
    masterUsername: ${MASTER_USERNAME:-admin}
    allocatedStorage: ${STORAGE_SIZE:-20}
    publiclyAccessible: ${PUBLICLY_ACCESSIBLE:-false}
    skipFinalSnapshot: true
    masterPasswordSecretRef:
      name: rds-password
      key: password
  providerConfigRef:
    name: default
EOF

            # Wait for RDS instance to be ready
            kubectl wait --for=condition=ready instance.rds.aws.crossplane.io/$INSTANCE_NAME --timeout=900s
            """,
            args=[
                Arg("instance_name",
                    description="Name of the RDS instance",
                    required=True),
                Arg("db_name",
                    description="Name of the database",
                    required=True),
                Arg("engine",
                    description="Database engine (defaults to postgres)",
                    required=False),
                Arg("engine_version",
                    description="Engine version (defaults to 14.7)",
                    required=False),
                Arg("instance_class",
                    description="Instance class (defaults to db.t3.micro)",
                    required=False),
                Arg("master_username",
                    description="Master username (defaults to admin)",
                    required=False),
                Arg("storage_size",
                    description="Allocated storage in GB (defaults to 20)",
                    required=False),
                Arg("publicly_accessible",
                    description="Whether the instance is publicly accessible (defaults to false)",
                    required=False)
            ],
            image="bitnami/kubectl:latest"
        )

    def list_resources(self) -> CrossplaneTool:
        """List all AWS resources managed by Crossplane."""
        return CrossplaneTool(
            name="list_aws_resources",
            description="List all AWS resources managed by Crossplane",
            content="""
            echo "=== AWS EKS Clusters ==="
            kubectl get clusters.eks.aws.crossplane.io

            echo "\n=== AWS S3 Buckets ==="
            kubectl get buckets.s3.aws.crossplane.io

            echo "\n=== AWS RDS Instances ==="
            kubectl get instances.rds.aws.crossplane.io

            echo "\n=== AWS VPCs ==="
            kubectl get vpcs.ec2.aws.crossplane.io

            echo "\n=== AWS IAM Roles ==="
            kubectl get roles.iam.aws.crossplane.io
            """,
            args=[],
            image="bitnami/kubectl:latest"
        ) 