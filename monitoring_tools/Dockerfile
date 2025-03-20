FROM python:3.9-slim

# Install dependencies
RUN pip install --no-cache-dir \
    slack-sdk \
    grafana-api \
    requests \
    python-dateutil

# Copy source code
COPY . /app
WORKDIR /app

# Install the package
RUN pip install -e . 