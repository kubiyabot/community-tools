FROM python:3.8-alpine

WORKDIR /report_tool

RUN apk add --no-cache --virtual .build-deps gcc musl-dev
RUN pip install --upgrade pip

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "-m", "report_tool"]