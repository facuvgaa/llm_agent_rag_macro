from kafka import KafkaConsumer
from controller import run_second_phase
import os
import subprocess
import json
import logging
import time
import docker

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


KAFKA_BROKER = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka_service:9092")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "etl-events")


def wait_for_kafka(max_retries=30, retry_interval=2):
    """Wait for Kafka to be available"""
    import socket
    logger.info("Esperando a que Kafka esté disponible...")
    
    host, port = KAFKA_BROKER.split(":")
    port = int(port)
    
    for attempt in range(max_retries):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex((host, port))
            sock.close()
            if result == 0:
                logger.info(f"✅ Kafka está disponible en {KAFKA_BROKER}")
                return True
        except Exception as e:
            logger.debug(f"Intento {attempt + 1}: Kafka no está disponible aún: {e}")
        
        logger.info(f"Esperando a Kafka... intento {attempt + 1}/{max_retries}")
        time.sleep(retry_interval)
    
    logger.error(f"❌ No se pudo conectar a Kafka después de {max_retries} intentos")
    return False


def main ():
    # Wait for Kafka to be ready
    if not wait_for_kafka():
        logger.error("No se pudo conectar a Kafka. Saliendo...")
        return
    
    # Inicializar cliente de Docker
    client = docker.from_env()
    
    consumer = KafkaConsumer(KAFKA_TOPIC, 
                        bootstrap_servers=[KAFKA_BROKER], 
                        group_id = 'controller_group',
                        auto_offset_reset='latest',
                        value_deserializer=lambda m: json.loads(m.decode("utf-8"))
                        )

    for message in consumer:

        data = message.value
        logger.info(f"mensaje recibido: {data}")
    
        if data.get("event") == "etl_done":
            logger.info("✅ ETL finalizado. Evento recibido correctamente.")
            logger.info("📝 Para cambiar al stack RAG, ejecutar manualmente:")
            logger.info("   cd /home/facuvega/Documentos/agent-full")
            logger.info("   docker compose -f infra/docker-compose.etl.yml down")
            logger.info("   docker compose -f infra/docker-compose.rag.yml up -d")
            
            # Ejecutar la segunda fase (solo notificación)
            try:
                run_second_phase(data)
                logger.info("🚀 Notificación enviada a la segunda fase ...")
            except Exception as e:
                logger.error(f"❌ Error en segunda fase: {e}")


if __name__ == "__main__":
    main()


