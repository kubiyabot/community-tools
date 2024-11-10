FROM alpine:3.14

# Install dependencies silently
RUN apk add --no-cache --quiet nodejs npm curl jq bash > /dev/null 2>&1

# Install mermaid-cli silently
RUN npm install -g @mermaid-js/mermaid-cli > /dev/null 2>&1

# Install slack-cli silently
RUN curl -s -L -o /usr/local/bin/slack https://raw.githubusercontent.com/rockymadden/slack-cli/master/src/slack \
    && chmod +x /usr/local/bin/slack