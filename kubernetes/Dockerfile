FROM bitnami/kubectl:latest

# Install required packages
RUN install_packages python3 python3-pip python3-venv curl jq

# Install Python packages
COPY requirements.txt /tmp/requirements.txt
RUN pip3 install --no-cache-dir -r /tmp/requirements.txt

# Copy scripts
COPY . /app
WORKDIR /app

CMD ["python3", "-m", "k8s_tools"]
