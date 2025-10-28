import logging
import requests
import os

logger = logging.getLogger(__name__)

def run_second_phase(event):
    """
    Ejecuta la segunda fase del Macro RAG.
    Puede llamar un microservicio, endpoint o script.
    """
    try:
        logger.info("🌐 Iniciando segunda fase del flujo...")

        gateway_url = os.getenv("GATEWAY_URL", "http://gateway_service:8000/start")
        response = requests.post(gateway_url, json={"event": event})
        
        if response.status_code == 200:
            logger.info("✅ Segunda fase ejecutada correctamente.")
        else:
            logger.error(f"❌ Error en gateway: {response.status_code} {response.text}")

    except Exception as e:
        logger.error(f"💥 Falló la segunda fase: {e}")