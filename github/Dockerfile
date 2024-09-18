FROM maniator/gh:latest

RUN yum update -y && yum install -y python3 python3-pip

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "-m", "github_tools"]
