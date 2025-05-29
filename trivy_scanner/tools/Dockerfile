FROM openshift/origin-cli:latest

# Install Trivy using official script
RUN sh -c "$(curl -fsSL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh)" -- -b /usr/local/bin v0.59.1 