FROM python:3.11-slim


RUN pip install torch transformers sentence-transformers fastapi uvicorn


CMD ["uvicorn", "main:app"]