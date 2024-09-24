FROM python:3.8-alpine

RUN apk update && apk add --no-cache python3 py3-pip git

COPY requirements.txt /tmp/requirements.txt
RUN pip3 install -r /tmp/requirements.txt

COPY . /report-tool
WORKDIR /report-tool

CMD ["python3", "-m", "report-tool"]