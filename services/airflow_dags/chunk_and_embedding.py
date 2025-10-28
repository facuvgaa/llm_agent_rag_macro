from pdf_chunk_flow import MacroEtlPdfChunks
from embedding_flow.transform.transform import transform_embedding
from embedding_flow.load.load import load_embedding
import pendulum
from confluent_kafka import Producer
import redis
import json
import hashlib
from datetime import timedelta
from airflow.decorators import dag, task
import os
import logging
import pandas as pd

REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
KAFKA_BROKER = os.getenv("KAFKA_BROKER", "kafka:9092")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "etl-events")

r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

# Confluent Kafka Producer configuration
producer = Producer({
    'bootstrap.servers': KAFKA_BROKER,
    'client.id': 'airflow-etl-producer'
})


logger = logging.getLogger(__name__)

URLS_FILE = os.path.join(os.path.dirname(__file__), "urls.txt")

@dag(
    dag_id="chunkear_and_embedding",
    schedule="@daily",
    start_date=pendulum.datetime(2025, 6, 24, tz="America/Argentina/Tucuman"),
    catchup=False,
    default_args={"retries": 1, "retry_delay": timedelta(minutes=5)},
    tags=["etl", "embedding", "pdf", "redis", "qdrant", "kafka"],
)
def chunkear_and_embedding():
    """
    DAG que:
    1️⃣ Lee URLs desde urls.txt
    2️⃣ Evita reprocesar PDFs usando Redis
    3️⃣ Chunkifica los PDFs en Parquet
    4️⃣ Genera embeddings y los carga en Qdrant
    5️⃣ Publica evento 'etl_done' en Kafka
    """

    @task()
    def leer_urls():
        """Lee el archivo urls.txt y devuelve la lista de URLs"""
        with open(URLS_FILE, "r") as f:
            urls = [line.strip() for line in f.readlines() if line.strip()]
        return urls

    @task()
    def chunkear_pdfs(urls: list):
        """Ejecuta el ETL de chunking de PDFs y retorna lista de parquets"""
        parquet_paths = []
        for url in urls:
            url_hash = hashlib.md5(url.encode()).hexdigest()
            
            if r.sismember("processed_urls", url_hash):
                logger.info(f"pdf ya procesado: {url}")
                continue
            
            parquet_path = MacroEtlPdfChunks(url)
            if parquet_path is None:
                raise Exception(f"❌ Error al procesar PDF desde {url}")
            
            r.sadd("processed_urls", url_hash)
            parquet_paths.append(parquet_path)
            logger.info(f"✅ PDF chunkificado: {url}")

        return parquet_paths

    @task()
    def generar_embeddings(parquet_paths: list):
        """Genera embeddings desde los Parquets y los carga en Qdrant"""
        results = []
        
        # Inicializar loader una sola vez (reutiliza conexión a Qdrant)
        loader = load_embedding()
        
        for parquet_path in parquet_paths:
            try:
                # 0️⃣ Preparar: renombrar columna chunk_text a text
                df = pd.read_parquet(parquet_path)
                if 'chunk_text' in df.columns:
                    df = df.rename(columns={'chunk_text': 'text'})
                    # Guardar temporalmente con la columna renombrada
                    temp_parquet = parquet_path.replace('.parquet', '_temp.parquet')
                    df.to_parquet(temp_parquet, index=False)
                    parquet_to_process = temp_parquet
                else:
                    parquet_to_process = parquet_path
                
                # 1️⃣ Transformar: generar embeddings
                transformer = transform_embedding()
                embedded_parquet = transformer.transform_data(parquet_to_process)
                
                if embedded_parquet is None:
                    raise Exception(f"Error al generar embeddings")
                
                # 2️⃣ Cargar: subir a Qdrant
                success = loader.load_data(embedded_parquet)
                
                if not success:
                    raise Exception(f"Error al cargar embeddings a Qdrant")
                
                results.append(embedded_parquet)
                logger.info(f"✅ Procesado: {parquet_path} -> {embedded_parquet}")
                
                # Limpiar archivo temporal
                if 'temp_parquet' in locals() and os.path.exists(temp_parquet):
                    os.remove(temp_parquet)
                
            except Exception as e:
                logger.error(f"❌ Error procesando {parquet_path}: {e}")
                raise Exception(f"❌ Error al procesar {parquet_path}: {e}")
        
        return f"✅ {len(results)} archivos procesados correctamente"

    @task()
    def publicar_evento_kafka(processed_count):
        """Publica evento 'etl_done' en Kafka"""
        data = {
            "event": "etl_done",
            "timestamp":  pendulum.now().to_iso8601_string(),
            "processed_count": processed_count,
        }
        
        # Convert data to JSON string
        message_value = json.dumps(data)
        
        # Send message using confluent-kafka
        producer.produce(
            topic=KAFKA_TOPIC,
            value=message_value.encode('utf-8')
        )
        producer.flush()
        logger.info(f"🚀 Evento publicado en Kafka: {data}")

    # Flujo del DAG
    urls = leer_urls()
    parquet_paths = chunkear_pdfs(urls)
    processed_count = generar_embeddings(parquet_paths)
    publicar_evento_kafka(processed_count)

# Inicializa el DAG
chunkear_and_embedding()