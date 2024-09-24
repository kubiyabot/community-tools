FROM google/cloud-sdk:latest

RUN apt-get update && apt-get install -y python3 python3-pip

WORKDIR /app

COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python3", "-m", "gcp_tools"]