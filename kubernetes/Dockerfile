FROM python:3.9-slim

# Install required system packages and kubectl/helm
RUN apt-get update && apt-get install -y \
    curl \
    apt-transport-https \
    gnupg2 \
    bash \
    && rm -rf /var/lib/apt/lists/* \
    && curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl" \
    && chmod +x kubectl \
    && mv kubectl /usr/local/bin/ \
    && curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "-m", "k8s_tools"]
