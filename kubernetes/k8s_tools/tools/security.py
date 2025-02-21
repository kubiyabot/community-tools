from kubiya_sdk.tools import Arg
from .base import KubernetesTool
from kubiya_sdk.tools.registry import tool_registry

check_privileged_pods_tool = KubernetesTool(
    name="check_privileged_pods",
    description="Identifies pods running with privileged security contexts or root access",
    content="""
    #!/bin/bash
    set -e

    # Set namespace flag based on input, with proper variable reference
    namespace_flag=$( [ -n "${1:-}" ] && echo "-n $1" || echo "--all-namespaces" )

    echo "🔍 Scanning for security risks in pods..."
    echo "========================================="

    echo "\n🔐 Pods running as root or with privileged security contexts:"
    kubectl get pods $namespace_flag -o json | jq -r '
        .items[] | 
        select(
            .spec.containers[].securityContext.privileged == true or
            .spec.containers[].securityContext.runAsUser == 0 or
            .spec.securityContext.runAsUser == 0
        ) |
        "  ⚠️  Namespace: \(.metadata.namespace)\n     Pod: \(.metadata.name)\n     Reason: \(
            if .spec.containers[].securityContext.privileged == true then "Privileged container"
            elif .spec.containers[].securityContext.runAsUser == 0 then "Container running as root"
            elif .spec.securityContext.runAsUser == 0 then "Pod running as root"
            else "Unknown security issue"
            end
        )"
    '

    echo "\n🛡️ Pods without security contexts defined:"
    kubectl get pods $namespace_flag -o json | jq -r '
        .items[] | 
        select(
            .spec.securityContext == null and
            (.spec.containers[] | select(.securityContext == null))
        ) |
        "  ⚠️  \(.metadata.namespace)/\(.metadata.name)"
    '
    """,
    args=[
        Arg(name="namespace", type="str", description="Kubernetes namespace to scan. If omitted, scans all namespaces.", required=False),
    ],
)

check_resource_limits_tool = KubernetesTool(
    name="check_resource_limits",
    description="Identifies pods/deployments running without resource limits set",
    content="""
    #!/bin/bash
    set -e

    # Set namespace flag based on input, with proper variable reference
    namespace_flag=$( [ -n "${1:-}" ] && echo "-n $1" || echo "--all-namespaces" )

    echo "📊 Scanning for missing resource limits..."
    echo "========================================"

    echo "\n⚠️ Pods without resource limits:"
    kubectl get pods $namespace_flag -o json | jq -r '
        .items[] | 
        select(
            .spec.containers[] | 
            select(.resources.limits == null or .resources.requests == null)
        ) |
        "  🚨 Namespace: \(.metadata.namespace)\n     Pod: \(.metadata.name)\n     Container(s): \(
            [.spec.containers[] | 
            select(.resources.limits == null or .resources.requests == null) | 
            .name] | join(", ")
        )"
    '

    echo "\n⚠️ Deployments without resource limits:"
    kubectl get deployments $namespace_flag -o json | jq -r '
        .items[] | 
        select(
            .spec.template.spec.containers[] | 
            select(.resources.limits == null or .resources.requests == null)
        ) |
        "  🚨 Namespace: \(.metadata.namespace)\n     Deployment: \(.metadata.name)\n     Container(s): \(
            [.spec.template.spec.containers[] | 
            select(.resources.limits == null or .resources.requests == null) | 
            .name] | join(", ")
        )"
    '
    """,
    args=[
        Arg(name="namespace", type="str", description="Kubernetes namespace to scan. If omitted, scans all namespaces.", required=False),
    ],
)

check_network_policies_tool = KubernetesTool(
    name="check_network_policies",
    description="Identifies namespaces and pods without network policies",
    content="""
    #!/bin/bash
    set -e

    # Set namespace flag based on input
    namespace_flag=$( [ -n "$namespace" ] && echo "-n $namespace" || echo "--all-namespaces" )

    echo "🌐 Scanning network policies..."
    echo "=============================="

    echo "\n📡 Namespaces without network policies:"
    if [ -n "$namespace" ]; then
        # Check only the specified namespace
        if [ $(kubectl get netpol -n "$namespace" -o json | jq '.items | length') -eq 0 ]; then
            echo "  ⚠️  $namespace"
        fi
    else
        # Check all namespaces
        kubectl get ns -o json | jq -r '
            .items[] | 
            select(
                .metadata.name as $ns | 
                ($ns != "kube-system" and $ns != "kube-public" and $ns != "kube-node-lease")
            ) |
            .metadata.name' | 
        while read ns; do
            if [ $(kubectl get netpol -n $ns -o json | jq '.items | length') -eq 0 ]; then
                echo "  ⚠️  $ns"
            fi
        done
    fi

    echo "\n🔍 Pods potentially exposed (no matching network policies):"
    kubectl get pods $namespace_flag -o json | jq -r '
        .items[] | 
        select(.metadata.namespace as $ns | 
            $ns != "kube-system" and 
            $ns != "kube-public" and 
            $ns != "kube-node-lease"
        ) |
        "  ⚠️  \(.metadata.namespace)/\(.metadata.name)"
    '
    """,
    args=[
        Arg(name="namespace", type="str", description="Kubernetes namespace to scan. If omitted, scans all namespaces.", required=False),
    ],
)

check_exposed_services_tool = KubernetesTool(
    name="check_exposed_services",
    description="Identifies potentially exposed services and their configurations",
    content="""
    #!/bin/bash
    set -e

    # Set namespace flag based on input
    namespace_flag=$( [ -n "$namespace" ] && echo "-n $namespace" || echo "--all-namespaces" )

    echo "🌍 Scanning for exposed services..."
    echo "================================="

    echo "\n🔍 LoadBalancer and NodePort Services:"
    kubectl get services $namespace_flag -o json | jq -r '
        .items[] | 
        select(.spec.type == "LoadBalancer" or .spec.type == "NodePort") |
        "  ⚠️  Namespace: \(.metadata.namespace)\n     Service: \(.metadata.name)\n     Type: \(.spec.type)\n     Ports: \(
            [.spec.ports[] | 
            "\(if .nodePort then "NodePort: \(.nodePort)" else "" end) → \(.port)"] | 
            join(", ")
        )"
    '

    echo "\n🔍 Services without selector (potential security risk):"
    kubectl get services $namespace_flag -o json | jq -r '
        .items[] | 
        select(.spec.selector == null) |
        "  ⚠️  \(.metadata.namespace)/\(.metadata.name)"
    '
    """,
    args=[
        Arg(name="namespace", type="str", description="Kubernetes namespace to scan. If omitted, scans all namespaces.", required=False),
    ],
)

check_pod_security_tool = KubernetesTool(
    name="check_pod_security",
    description="Comprehensive security check for pods including volume mounts, capabilities, and security contexts",
    content="""
    #!/bin/bash
    set -e

    # Set namespace flag based on input
    namespace_flag=$( [ -n "$namespace" ] && echo "-n $namespace" || echo "--all-namespaces" )

    echo "🛡️ Running comprehensive pod security scan..."
    echo "=========================================="

    echo "\n📦 Pods with hostPath volumes:"
    kubectl get pods $namespace_flag -o json | jq -r '
        .items[] | 
        select(.spec.volumes[]?.hostPath != null) |
        "  ⚠️  Namespace: \(.metadata.namespace)\n     Pod: \(.metadata.name)\n     Volumes: \(
            [.spec.volumes[] | select(.hostPath != null) | .name] | join(", ")
        )"
    '

    echo "\n🔑 Pods with dangerous capabilities:"
    kubectl get pods $namespace_flag -o json | jq -r '
        .items[] | 
        select(
            .spec.containers[] | 
            select(.securityContext?.capabilities?.add? // [] | 
                any(. == "ALL" or . == "SYS_ADMIN" or . == "NET_ADMIN")
            )
        ) |
        "  ⚠️  Namespace: \(.metadata.namespace)\n     Pod: \(.metadata.name)\n     Capabilities: \(
            [.spec.containers[] | 
             .securityContext?.capabilities?.add? // [] | 
             select(. == "ALL" or . == "SYS_ADMIN" or . == "NET_ADMIN")] | join(", ")
        )"
    '

    echo "\n🎯 Pods with hostNetwork, hostPID, or hostIPC:"
    kubectl get pods $namespace_flag -o json | jq -r '
        .items[] | 
        select(
            .spec.hostNetwork == true or
            .spec.hostPID == true or
            .spec.hostIPC == true
        ) |
        "  ⚠️  Namespace: \(.metadata.namespace)\n     Pod: \(.metadata.name)\n     Issues: \(
            [
                if .spec.hostNetwork == true then "hostNetwork" else empty end,
                if .spec.hostPID == true then "hostPID" else empty end,
                if .spec.hostIPC == true then "hostIPC" else empty end
            ] | join(", ")
        )"
    '
    """,
    args=[
        Arg(name="namespace", type="str", description="Kubernetes namespace to scan. If omitted, scans all namespaces.", required=False),
    ],
)

full_security_scan_tool = KubernetesTool(
    name="full_security_scan",
    description="Performs a comprehensive security scan of the cluster, combining all security checks",
    content="""
    #!/bin/bash
    set -e

    # Set namespace flag based on input
    namespace_flag=$( [ -n "$namespace" ] && echo "-n $namespace" || echo "--all-namespaces" )

    echo "🔒 Starting comprehensive security scan..."
    echo "========================================"

    # Check privileged containers and root access
    echo "\n1️⃣ Checking privileged containers and root access..."
    kubectl get pods $namespace_flag -o json | jq -r '
        .items[] | 
        select(
            .spec.containers[].securityContext.privileged == true or
            .spec.containers[].securityContext.runAsUser == 0 or
            .spec.securityContext.runAsUser == 0
        ) |
        "  ⚠️  \(.metadata.namespace)/\(.metadata.name)"
    '

    # Check resource limits
    echo "\n2️⃣ Checking for missing resource limits..."
    kubectl get pods $namespace_flag -o json | jq -r '
        .items[] | 
        select(.spec.containers[] | select(.resources.limits == null)) |
        "  ⚠️  \(.metadata.namespace)/\(.metadata.name)"
    '

    # Check network policies
    echo "\n3️⃣ Checking network policies..."
    kubectl get ns -o json | jq -r '
        .items[] | 
        select(.metadata.name as $ns | 
            not(any(["kube-system", "kube-public", "kube-node-lease"]; . == $ns))
        ) |
        .metadata.name' | 
    while read ns; do
        if [ $(kubectl get netpol -n $ns -o json | jq '.items | length') -eq 0 ]; then
            echo "  ⚠️  Namespace without network policies: $ns"
        fi
    done

    # Check exposed services
    echo "\n4️⃣ Checking exposed services..."
    kubectl get services $namespace_flag -o json | jq -r '
        .items[] | 
        select(.spec.type == "LoadBalancer" or .spec.type == "NodePort") |
        "  ⚠️  Exposed service: \(.metadata.namespace)/\(.metadata.name) (Type: \(.spec.type))"
    '

    # Check security contexts and capabilities
    echo "\n5️⃣ Checking security contexts and capabilities..."
    kubectl get pods $namespace_flag -o json | jq -r '
        .items[] | 
        select(
            .spec.containers[].securityContext.capabilities.add != null or
            .spec.hostNetwork == true or
            .spec.hostPID == true or
            .spec.hostIPC == true
        ) |
        "  ⚠️  Pod with security risks: \(.metadata.namespace)/\(.metadata.name)"
    '

    echo "\n✅ Security scan complete!"
    """,
    args=[
        Arg(name="namespace", type="str", description="Kubernetes namespace to scan. If omitted, scans all namespaces.", required=False),
    ],
)

# Register all tools
for tool in [
    check_privileged_pods_tool,
    check_resource_limits_tool,
    check_network_policies_tool,
    check_exposed_services_tool,
    check_pod_security_tool,
    full_security_scan_tool,
]:
    tool_registry.register("kubernetes", tool) 