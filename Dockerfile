FROM python:3.10-slim

RUN apt-get update && apt-get install -y openssh-client

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .
COPY servers.yaml .
COPY keys/ ./keys/


CMD ["python", "main.py"]