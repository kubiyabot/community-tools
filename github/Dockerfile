# syntax=docker/dockerfile:1

ARG APPNAME=github_tools

FROM --platform=$BUILDPLATFORM python:3.11-alpine AS builder
LABEL org.opencontainers.image.authors="michael.bauer"

ARG APPNAME
ARG TARGETPLATFORM
ARG USERNAME=$APPNAME

WORKDIR /app

COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.11-alpine

ARG APPNAME=github_tools
ARG USERNAME=$APPNAME

# System deps
RUN apk add --no-cache jq ca-certificates curl socat gettext

# Install GitHub CLI
RUN apk add --no-cache github-cli

# Create app user
RUN addgroup -g 6009 $USERNAME && \
    adduser -D -G $USERNAME -u 6009 -h /app -s /sbin/nologin $USERNAME

# Copy dependencies from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Set proper permissions for Python executables and libraries
RUN find /usr/local/bin -type f -name "python*" -exec chmod 755 {} \;
RUN find /usr/local/bin -type f -name "pip*" -exec chmod 755 {} \;
RUN find /usr/local/lib/python3.11/site-packages -type d -exec chmod 755 {} \;
RUN find /usr/local/lib/python3.11/site-packages -type f -exec chmod 644 {} \;
RUN find /usr/local/lib/python3.11/site-packages -type f -name "*.so" -exec chmod 755 {} \;

# Copy source code
COPY . /app/

WORKDIR /app

# Set permissions
RUN chown -R $USERNAME:$USERNAME /app

USER $USERNAME

CMD ["/bin/sh"]
