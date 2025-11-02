FROM python:3.11-slim

WORKDIR /opt/embedding_service


COPY services/embedding_service/requirements.txt ./requirements.txt

RUN pip install --no-cache-dir torch==2.3.0+cpu -f https://download.pytorch.org/whl/torch_stable.html

RUN pip install --no-cache-dir -r requirements.txt

COPY services/embedding_service/app ./app

EXPOSE 8001
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
