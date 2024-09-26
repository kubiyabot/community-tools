FROM python:3.8-alpine
WORKDIR /report_tool

# Install pip using apk
RUN apk add --no-cache py3-pip

# Upgrade pip
RUN pip install --upgrade pip

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "-m", "report_tool"]