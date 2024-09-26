FROM python:3.8-slim

WORKDIR /report_tool

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "-m", "report_tool"]