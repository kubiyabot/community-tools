FROM alpine:3.18

# Install necessary packages
RUN apk add --no-cache \
    python3 \
    py3-pip \
    git \
    curl \
    jq

# Set working directory
WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Set the entrypoint
ENTRYPOINT ["python3", "-m", "pagerduty_alerting.tools"]
