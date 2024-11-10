FROM node:16-slim

# Install dependencies silently
RUN apt-get update -qq >/dev/null \
    && apt-get install -yqq bash curl jq >/dev/null \
    && npm install -g @mermaid-js/mermaid-cli >/dev/null \
    && curl -s -L -o /usr/local/bin/slack https://raw.githubusercontent.com/rockymadden/slack-cli/master/src/slack \
    && chmod +x /usr/local/bin/slack