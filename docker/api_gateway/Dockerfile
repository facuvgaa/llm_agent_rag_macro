FROM python:3.12-slim

WORKDIR /opt/api_gateway

COPY services/api_gateway/app/requirements.txt ./requirements.txt

RUN pip install --no-cache-dir -r requirements.txt

CMD ["uvicorn", "app.app:app", "--host", "0.0.0.0", "--port", "8000"]