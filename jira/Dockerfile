FROM aghcr.io/ankitpokhrel/jira-cli:latest

RUN yum update -y && yum install -y python3 python3-pip

COPY requirements.txt /tmp/requirements.txt
RUN pip3 install -r /tmp/requirements.txt

COPY . /jira_tools
WORKDIR /jira_tools

CMD ["python3", "-m", "jira_tools"]