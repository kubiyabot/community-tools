FROM amazon/aws-cli:latest

RUN yum update -y && yum install -y python3 python3-pip

COPY requirements.txt /tmp/requirements.txt
RUN pip3 install -r /tmp/requirements.txt

COPY . /aws_tools
WORKDIR /aws_tools

CMD ["python3", "-m", "aws_tools"]
