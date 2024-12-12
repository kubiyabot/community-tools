FROM python:3.9-slim

# Install sudo for apt operations
RUN apt-get update && apt-get install -y \
    sudo \
    bash \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "-m", "k8s_tools"]
