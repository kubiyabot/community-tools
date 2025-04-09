ARG APPNAME="github_tools"
FROM --platform=$BUILDPLATFORM python:3.11-slim AS builder
LABEL org.opencontainers.image.authors="michael.bauer"
ARG TARGETPLATFORM
ARG APPNAME
ARG USERNAME=$APPNAME

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.11-slim
ARG APPNAME
ARG USERNAME=$APPNAME

# Install minimal dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    jq \
    ca-certificates \
    curl \
    socat \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    # Create minimal user and group files
    && echo "$USERNAME:x:6009:6009:$USERNAME:/app:/sbin/nologin" >> /etc/passwd \
    && echo "$USERNAME:x:6009:" >> /etc/group

# Copy only necessary files from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY . /app/

WORKDIR /app
USER $USERNAME

# Default to shell if no command is provided
CMD ["/bin/bash"]
