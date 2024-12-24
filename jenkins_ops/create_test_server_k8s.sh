#!/bin/bash

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Function to print colored output
print_warning() { echo -e "${YELLOW}WARNING: $1${NC}"; }
print_error() { echo -e "${RED}ERROR: $1${NC}"; }
print_success() { echo -e "${GREEN}SUCCESS: $1${NC}"; }

# Check for existing Jenkins installation
check_existing_jenkins() {
    if kubectl get namespace jenkins >/dev/null 2>&1; then
        print_warning "Existing Jenkins installation found!"
        print_warning "This will DELETE your existing Jenkins installation and all its data."
        read -p "Do you want to proceed? (y/n): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            print_warning "Installation cancelled by user"
            exit 1
        fi
        
        print_warning "Removing existing Jenkins installation..."
        helm uninstall jenkins -n jenkins >/dev/null 2>&1
        kubectl delete namespace jenkins --wait=true >/dev/null 2>&1
        print_success "Existing Jenkins installation removed"
    fi
}

# Replace the wait_for_jenkins function with this improved version:

wait_for_jenkins() {
    echo "Waiting for Jenkins to be fully operational..."
    local retries=0
    local max_retries=30

    # First check if pod is ready
    echo "Checking pod status..."
    while ! kubectl get pods -n jenkins jenkins-0 -o jsonpath='{.status.phase}' | grep -q "Running"; do
        echo "Pod not yet running..."
        sleep 5
        retries=$((retries + 1))
        if [ $retries -gt $max_retries ]; then
            print_error "Pod failed to start"
            return 1
        fi
    done

    # Reset retry counter
    retries=0
    
    # Then check Jenkins web interface
    echo "Checking Jenkins web interface..."
    while true; do
        # Try to access Jenkins and store HTTP status code
        HTTP_CODE=$(curl -s -w '%{http_code}' -o /dev/null --user "admin:${ADMIN_PASSWORD}" \
            http://localhost:8080/login)
        
        # Check different HTTP status codes
        case $HTTP_CODE in
            200|403)
                echo "Jenkins is ready!"
                return 0
                ;;
            301|302)
                echo "Jenkins is redirecting, might be ready..."
                return 0
                ;;
            503)
                echo "Jenkins is starting up (Service Unavailable)..."
                ;;
            *)
                echo "Jenkins returned status code: $HTTP_CODE"
                ;;
        esac

        sleep 10
        retries=$((retries + 1))
        
        if [ $retries -gt $max_retries ]; then
            print_error "Jenkins failed to become ready (timeout)"
            echo "Debug information:"
            kubectl get pods -n jenkins
            kubectl describe pod -n jenkins jenkins-0
            kubectl logs -n jenkins jenkins-0
            return 1
        fi

        echo "Still waiting... Attempt $retries of $max_retries"
    done
}


# Function to create a pipeline job with CSRF handling
create_pipeline_job() {
    local job_name=$1
    local job_description=$2
    local pipeline_script=$3
    
    print_warning "Creating job: ${job_name}"
    
    # Get CSRF crumb
    local crumb_data=$(curl -s "http://localhost:8080/crumbIssuer/api/xml?xpath=concat(//crumbRequestField,\":\",//crumb)" \
        --user "admin:${ADMIN_PASSWORD}")
    
    if [ -z "$crumb_data" ]; then
        print_error "Failed to get CSRF crumb"
        return 1
    fi
    
    # Create Pipeline XML
    cat << EOF > "job_${job_name}.xml"
<?xml version='1.1' encoding='UTF-8'?>
<flow-definition plugin="workflow-job">
  <description>${job_description}</description>
  <keepDependencies>false</keepDependencies>
  <properties/>
  <definition class="org.jenkinsci.plugins.workflow.cps.CpsFlowDefinition" plugin="workflow-cps">
    <script>${pipeline_script}</script>
    <sandbox>true</sandbox>
  </definition>
  <triggers/>
  <disabled>false</disabled>
</flow-definition>
EOF

    # Create job using Jenkins API with CSRF crumb
    curl -XPOST "http://localhost:8080/createItem?name=${job_name}" \
        --user "admin:${ADMIN_PASSWORD}" \
        -H "${crumb_data}" \
        --header "Content-Type: application/xml" \
        --data-binary "@job_${job_name}.xml"

    # Clean up the temporary XML file
    rm "job_${job_name}.xml"
}

main() {
    # Check prerequisites
    if ! command -v kubectl >/dev/null 2>&1; then
        print_error "kubectl not found. Please install kubectl first."
        exit 1
    fi

    if ! command -v helm >/dev/null 2>&1; then
        print_error "helm not found. Please install helm first."
        exit 1
    fi

    # Check cluster connection
    if ! kubectl get nodes >/dev/null 2>&1; then
        print_error "Cannot connect to Kubernetes cluster. Please check your kubeconfig."
        exit 1
    fi

    # Check and handle existing installation
    check_existing_jenkins

    # Add Jenkins helm repo
    echo "Adding Jenkins Helm repository..."
    helm repo add jenkins https://charts.jenkins.io >/dev/null 2>&1
    helm repo update >/dev/null 2>&1

    # Create namespace
    kubectl create namespace jenkins

    # Generate random admin password
    ADMIN_PASSWORD=$(openssl rand -base64 12)

    # Create values file
    cat << EOF > jenkins-values.yaml
controller:
  admin:
    existingSecret: ""
    userKey: jenkins-admin-user
    passwordKey: jenkins-admin-password
    username: "admin"
    password: "${ADMIN_PASSWORD}"
  resources:
    requests:
      cpu: "500m"
      memory: "512Mi"
    limits:
      cpu: "2000m"
      memory: "2048Mi"
  installPlugins:
    - workflow-job:latest
    - workflow-cps:latest
    - workflow-aggregator:latest
    - cloudbees-folder:latest
  numExecutors: 2
persistence:
  enabled: true
  size: "8Gi"
serviceAccount:
  create: true
EOF

    # Install Jenkins
    echo "Installing Jenkins (this may take a few minutes)..."
    if ! helm install jenkins jenkins/jenkins -n jenkins -f jenkins-values.yaml --wait --timeout 10m0s; then
        print_error "Jenkins installation failed"
        kubectl delete namespace jenkins
        exit 1
    fi

    # Show pod status right after installation
    echo "Checking initial pod status..."
    kubectl get pods -n jenkins
    echo "Waiting 30 seconds for initial setup..."
    sleep 30
    
    # Setup port forwarding
    echo "Setting up port forwarding..."
    if lsof -i :8080 >/dev/null 2>&1; then
        print_warning "Port 8080 is already in use. Killing existing process..."
        lsof -ti :8080 | xargs kill -9 2>/dev/null
    fi

    kubectl port-forward -n jenkins svc/jenkins 8080:8080 &
    PORT_FORWARD_PID=$!

    # Wait for port-forward to establish
    sleep 5

    # Get different access URLs
    CLUSTER_IP=$(kubectl get svc jenkins -n jenkins -o jsonpath='{.spec.clusterIP}')
    NODE_PORT=$(kubectl get svc jenkins -n jenkins -o jsonpath='{.spec.ports[0].port}')
    NAMESPACE="jenkins"
    SERVICE_NAME="jenkins"

    # Wait for Jenkins to be fully operational
    if ! wait_for_jenkins; then
        print_error "Failed to connect to Jenkins"
        exit 1
    fi

    echo "Creating example jobs..."
    sleep 10  # Give Jenkins a moment to settle

    # Create example jobs
    create_pipeline_job "ci-pipeline" "Basic CI Pipeline" 'pipeline {
        agent any
        stages {
            stage("Build") {
                steps {
                    echo "Building..."
                    sh "echo Build time: \$(date)"
                }
            }
            stage("Test") {
                steps {
                    echo "Testing..."
                    sh "echo Test time: \$(date)"
                }
            }
        }
    }'

    create_pipeline_job "deploy" "Deployment Pipeline" 'pipeline {
        agent any
        stages {
            stage("Deploy") {
                steps {
                    echo "Deploying..."
                    sh "echo Deploy time: \$(date)"
                }
            }
        }
    }'

    create_pipeline_job "backup" "Backup Pipeline" 'pipeline {
        agent any
        triggers { cron("0 0 * * *") }
        stages {
            stage("Backup") {
                steps {
                    echo "Backing up..."
                    sh "echo Backup time: \$(date)"
                }
            }
        }
    }'

    # Save credentials to a file
    cat << EOF > jenkins-credentials.env
# Jenkins Credentials
# Run: source jenkins-credentials.env
JENKINS_URL=http://$SERVICE_NAME.$NAMESPACE.svc.cluster.local:$NODE_PORT
JENKINS_USER=admin
JENKINS_PASS=$ADMIN_PASSWORD
EOF

    chmod 600 jenkins-credentials.env

    # Print success information
    print_success "Jenkins has been installed successfully!"
    echo "============================================"
    echo "Access Methods:"
    echo ""
    echo "1. Local Port Forward (Current):"
    echo "   URL: http://localhost:8080"
    echo ""
    echo "2. In-Cluster Access:"
    echo "   URL: http://$SERVICE_NAME.$NAMESPACE.svc.cluster.local:$NODE_PORT"
    echo "   URL: http://$CLUSTER_IP:$NODE_PORT"
    echo ""
    echo "Credentials:"
    echo "Username: admin"
    echo "Password: $ADMIN_PASSWORD"
    echo "============================================"
    echo "For team members, share these environment variables:"
    echo "source jenkins-credentials.env"
    echo "============================================"
    echo "Example jobs have been created:"
    echo "1. ci-pipeline"
    echo "2. deploy"
    echo "3. backup"
    echo "============================================"
    echo "Port forwarding is active. To stop it, run:"
    echo "kill $PORT_FORWARD_PID"
    echo "============================================"

    # Keep script running until user interrupts
    trap "kill $PORT_FORWARD_PID 2>/dev/null" EXIT
    wait
}

# Run main function
main