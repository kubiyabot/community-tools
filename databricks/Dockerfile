FROM hashicorp/terraform:latest

RUN apk update && apk add --no-cache python3 py3-pip git

COPY requirements.txt /tmp/requirements.txt
RUN pip3 install -r /tmp/requirements.txt

COPY . /databricks_workspace_iac
WORKDIR /databricks_workspace_iac

CMD ["python3", "-m", "databricks_workspace_iac"]