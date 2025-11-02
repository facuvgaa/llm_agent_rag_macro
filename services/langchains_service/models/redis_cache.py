import redis
import json
import os
from typing import Optional 
import hashlib

REDIS_HOST = os.getenv("REDIS_HOST", "redis_service")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
CACHE_TTL = int(os.getenv("CACHE_TTL", 3600))

class RedisCache:
    """Cache de respuestas usando Redis"""

    def __init__(self):
        try:
            self.client = redis.Redis(
                host=REDIS_HOST, 
                port=REDIS_PORT, 
                decode_responses=True,
                socket_connect_timeout=5
            )
            self.client.ping()
            self.connected = True
        except Exception as e:
            print(f"Error al conectar a Redis: {e}")
            self.connected = False

    def _generate_key(self, question: str) -> str:
        """Genera una clave única para la pregunta"""
        normalized = question.lower().strip()
        hash_obj = hashlib.sha256(normalized.encode())
        return f"cache:question:{hash_obj.hexdigest()}"

    def get_cached_answer(self, question: str) -> Optional[str]:
        """Obtiene respuesta cacheada si existe"""
        if not self.connected:
            return None
        
        try:
            key = self._generate_key(question)
            cached = self.client.get(key)
            if cached:
                data = json.loads(cached)
                return data.get("answer")
        except Exception as e:
            print(f"Error al obtener la respuesta cacheada: {e}")

        return None

    def cache_answer(self, question: str, answer: str, ttl: int = None):
        """Guarda respuesta en cache"""
        if not self.connected:
            return
        try:
            key = self._generate_key(question)
            data = {
                "question": question,
                "answer": answer,
            }
            ttl = ttl or CACHE_TTL
            self.client.setex(key, ttl, json.dumps(data))
        except Exception as e:
            print(f"Error al cachear la respuesta: {e}")

    def get_conversation_cache(self, thread_id: str) -> list:
        """Obtiene historial de conversación desde Redis"""
        if not self.connected:
            return []

        try:
            key = f"conversation:{thread_id}"    
            cached = self.client.lrange(key, 0, -1)
            return [json.loads(item) for item in cached]
        except Exception as e:
            print(f"Error obteniendo historial: {e}")
            return []

    def save_to_conversation(self, thread_id: str, question: str, answer: str):
        """Guarda mensaje en historial de conversación"""
        if not self.connected:
            return
        
        try:
            key = f"conversation:{thread_id}"
            data = {"question": question, "answer": answer}
            # Primero agregar el mensaje
            self.client.rpush(key, json.dumps(data))
            # Luego mantener solo últimas 50 mensajes
            self.client.ltrim(key, -50, -1)
            # Expirar después de 7 días
            self.client.expire(key, 604800)
        except Exception as e:
            print(f"Error guardando en historial: {e}")


redis_cache = RedisCache()
