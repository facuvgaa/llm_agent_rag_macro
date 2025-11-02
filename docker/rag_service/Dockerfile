FROM python:3.11-slim

WORKDIR opt/embedding_service

COPY ../../service/rag_service/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY ../../services/embedding/app ./app

EXPOSE 8001

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
