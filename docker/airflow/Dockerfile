FROM apache/airflow:slim-3.0.4rc2-python3.12

# Install PyTorch first (CPU version)
RUN pip install --no-cache-dir torch==2.3.1 torchvision --index-url https://download.pytorch.org/whl/cpu

# Copy requirements file
COPY requirements.txt /requirements.txt

# Install custom packages first (without dependencies)
RUN pip install --no-cache-dir pdf-chunk-flow embedding-flow --no-deps

# Install all other dependencies from requirements.txt
RUN pip install --no-cache-dir -r /requirements.txt

CMD ["airflow", "standalone"]

