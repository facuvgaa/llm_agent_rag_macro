FROM python:3.12-slim

WORKDIR /opt/controller_service

# Copia solo requirements (que ahora sí está en el contexto)
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# No copiamos el código fuente porque se monta con volumes
CMD ["python", "app/main.py"]

