from typing import List
from ..base import CrossplaneTool, Arg

class GCPProviderManager(CrossplaneTool):
    """Manage GCP-specific Crossplane provider operations."""
    
    def __init__(self):
        super().__init__(
            name="gcp_provider",
            description="Manage GCP provider and resources",
            content="",
            args=[],
            image="bitnami/kubectl:latest",
            mermaid="""
```mermaid
classDiagram
    class CrossplaneTool {
        <<base>>
    }
    class GCPProviderManager {
        +install_provider()
        +configure_credentials()
        +create_gke_cluster()
        +create_cloud_sql()
        +create_storage_bucket()
        +create_vpc()
        +list_resources()
    }
    CrossplaneTool <|-- GCPProviderManager
    note for GCPProviderManager "Manages GCP-specific\nresources and configurations"
```
"""
        )

    def install_provider(self) -> CrossplaneTool:
        """Install GCP provider."""
        return CrossplaneTool(
            name="install_gcp_provider",
            description="Install GCP provider and its CRDs",
            content="""
            # Install GCP provider
            cat <<EOF | kubectl apply -f -
apiVersion: pkg.crossplane.io/v1
kind: Provider
metadata:
  name: provider-gcp
spec:
  package: xpkg.upbound.io/upbound/provider-gcp:v0.37.0
EOF

            # Wait for provider to be healthy
            kubectl wait --for=condition=healthy provider.pkg.crossplane.io/provider-gcp --timeout=300s
            """,
            args=[],
            image="bitnami/kubectl:latest"
        )

    def configure_credentials(self) -> CrossplaneTool:
        """Configure GCP credentials."""
        return CrossplaneTool(
            name="configure_gcp_credentials",
            description="Configure GCP provider credentials",
            content="""
            if [ -z "$GCP_CREDS" ]; then
                echo "Error: GCP credentials file not specified"
                exit 1
            fi

            # Create secret from credentials file
            kubectl create secret generic gcp-creds -n crossplane-system --from-file=creds="$GCP_CREDS"

            # Create ProviderConfig
            cat <<EOF | kubectl apply -f -
apiVersion: gcp.crossplane.io/v1beta1
kind: ProviderConfig
metadata:
  name: default
spec:
  projectID: ${PROJECT_ID}
  credentials:
    source: Secret
    secretRef:
      namespace: crossplane-system
      name: gcp-creds
      key: creds
EOF
            """,
            args=[
                Arg("gcp_creds",
                    description="Path to GCP credentials JSON file",
                    required=True),
                Arg("project_id",
                    description="GCP project ID",
                    required=True)
            ],
            image="bitnami/kubectl:latest"
        )

    def create_gke_cluster(self) -> CrossplaneTool:
        """Create a GKE cluster."""
        return CrossplaneTool(
            name="create_gke_cluster",
            description="Create a GCP GKE cluster",
            content="""
            if [ -z "$CLUSTER_NAME" ]; then
                echo "Error: Cluster name not specified"
                exit 1
            fi

            cat <<EOF | kubectl apply -f -
apiVersion: container.gcp.crossplane.io/v1beta1
kind: Cluster
metadata:
  name: $CLUSTER_NAME
spec:
  forProvider:
    location: ${LOCATION:-us-central1}
    initialClusterVersion: ${VERSION:-1.27}
    network: ${NETWORK:-default}
    subnetwork: ${SUBNETWORK:-default}
    ipAllocationPolicy:
      useIpAliases: true
    masterAuth:
      clientCertificateConfig:
        issueClientCertificate: false
  providerConfigRef:
    name: default
EOF

            # Wait for cluster to be ready
            kubectl wait --for=condition=ready cluster.container.gcp.crossplane.io/$CLUSTER_NAME --timeout=900s
            """,
            args=[
                Arg("cluster_name",
                    description="Name of the GKE cluster",
                    required=True),
                Arg("location",
                    description="GCP location (defaults to us-central1)",
                    required=False),
                Arg("version",
                    description="Kubernetes version (defaults to 1.27)",
                    required=False),
                Arg("network",
                    description="VPC network name",
                    required=False),
                Arg("subnetwork",
                    description="VPC subnetwork name",
                    required=False)
            ],
            image="bitnami/kubectl:latest"
        )

    def create_storage_bucket(self) -> CrossplaneTool:
        """Create a GCS bucket."""
        return CrossplaneTool(
            name="create_storage_bucket",
            description="Create a GCP Storage bucket",
            content="""
            if [ -z "$BUCKET_NAME" ]; then
                echo "Error: Bucket name not specified"
                exit 1
            fi

            cat <<EOF | kubectl apply -f -
apiVersion: storage.gcp.crossplane.io/v1beta1
kind: Bucket
metadata:
  name: $BUCKET_NAME
spec:
  forProvider:
    location: ${LOCATION:-US}
    storageClass: ${STORAGE_CLASS:-STANDARD}
    versioning:
      enabled: true
  providerConfigRef:
    name: default
EOF

            # Wait for bucket to be ready
            kubectl wait --for=condition=ready bucket.storage.gcp.crossplane.io/$BUCKET_NAME --timeout=300s
            """,
            args=[
                Arg("bucket_name",
                    description="Name of the GCS bucket",
                    required=True),
                Arg("location",
                    description="Bucket location (defaults to US)",
                    required=False),
                Arg("storage_class",
                    description="Storage class (defaults to STANDARD)",
                    required=False)
            ],
            image="bitnami/kubectl:latest"
        )

    def list_resources(self) -> CrossplaneTool:
        """List all GCP resources managed by Crossplane."""
        return CrossplaneTool(
            name="list_gcp_resources",
            description="List all GCP resources managed by Crossplane",
            content="""
            echo "=== GCP GKE Clusters ==="
            kubectl get clusters.container.gcp.crossplane.io

            echo "\n=== GCP Storage Buckets ==="
            kubectl get buckets.storage.gcp.crossplane.io

            echo "\n=== GCP Cloud SQL Instances ==="
            kubectl get instances.sql.gcp.crossplane.io

            echo "\n=== GCP VPC Networks ==="
            kubectl get networks.compute.gcp.crossplane.io

            echo "\n=== GCP Service Accounts ==="
            kubectl get serviceaccounts.iam.gcp.crossplane.io
            """,
            args=[],
            image="bitnami/kubectl:latest"
        ) 