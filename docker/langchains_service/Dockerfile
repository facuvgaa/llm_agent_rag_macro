FROM python:3.12-slim

WORKDIR /opt/langchains_service

COPY services/langchains_service/requirements.txt ./requirements.txt

RUN pip install --no-cache-dir -r requirements.txt

COPY services/langchains_service ./

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]