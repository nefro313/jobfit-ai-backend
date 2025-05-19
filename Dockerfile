# 1) Base image
FROM python:3.11-slim

WORKDIR /backend
COPY . /backend

RUN apt update -y && apt install awscli -y

RUN pip install -r requirements.txt

# 5) Copy application code


CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
