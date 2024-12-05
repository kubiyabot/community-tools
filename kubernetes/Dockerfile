FROM python:3.9-slim

# Install required system packages
RUN apt-get update && apt-get install -y \
    curl \
    apt-transport-https \
    gnupg2 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Install the package
RUN pip install -e .

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV KUBERNETES_SERVICE_HOST=kubernetes.default.svc
ENV KUBERNETES_SERVICE_PORT=443

# Run initialization and start application
CMD ["python", "-m", "k8s_tools"]
