import os
import httpx
import time
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from langchain_core.embeddings import Embeddings
from typing import List, Optional

QDRANT_URL = os.getenv("QDRANT_URL", "http://qdrant:6333")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", "dev_key_123")
EMBEDDING_SERVICE_URL = os.getenv("EMBEDDING_SERVICE_URL", "http://embedding_service:8001/embedding")
DOCS_COLLECTION = os.getenv("QDRANT_COLLECTION_DOCS", "embeddings_collection")
CONVERSATIONS_COLLECTION = os.getenv("QDRANT_COLLECTION_CONVERSATIONS", "conversations")

class RemoteEmbeddingFunction(Embeddings):
    def embed_query(self, text: str) -> List[float]:
        response = httpx.post(EMBEDDING_SERVICE_URL, json={"texts": [text]}, timeout=60)
        response.raise_for_status()
        return response.json()[0] 

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        response = httpx.post(EMBEDDING_SERVICE_URL, json={"texts": texts}, timeout=60)
        response.raise_for_status()
        return response.json()

# Variables globales para inicialización lazy
_embedding_function: Optional[RemoteEmbeddingFunction] = None
_client: Optional[QdrantClient] = None
_qdrant_docs: Optional[QdrantVectorStore] = None
_qdrant_conversations: Optional[QdrantVectorStore] = None

def _get_client() -> QdrantClient:
    """Obtiene o crea el cliente de Qdrant con retry logic."""
    global _client
    if _client is None:
        max_retries = 5
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                _client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY, timeout=10)
                # Verificar conexión
                _client.get_collections()
                return _client
            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"Error conectando a Qdrant (intento {attempt + 1}/{max_retries}): {e}. Reintentando...")
                    time.sleep(retry_delay)
                else:
                    raise Exception(f"No se pudo conectar a Qdrant después de {max_retries} intentos: {e}")
    return _client

def _get_embedding_function() -> RemoteEmbeddingFunction:
    """Obtiene o crea la función de embeddings."""
    global _embedding_function
    if _embedding_function is None:
        _embedding_function = RemoteEmbeddingFunction()
    return _embedding_function

def get_qdrant_docs() -> QdrantVectorStore:
    """Obtiene o crea el vector store de documentos."""
    global _qdrant_docs
    if _qdrant_docs is None:
        client = _get_client()
        embedding_function = _get_embedding_function()
        _qdrant_docs = QdrantVectorStore(
            client=client,
            collection_name=DOCS_COLLECTION,
            embedding=embedding_function,
            content_payload_key="text",  # Campo del payload que contiene el texto
        )
    return _qdrant_docs

def get_qdrant_conversations() -> Optional[QdrantVectorStore]:
    """Obtiene o crea el vector store de conversaciones si existe."""
    global _qdrant_conversations
    if _qdrant_conversations is None:
        try:
            client = _get_client()
            embedding_function = _get_embedding_function()
            
            # Verificar si existe la colección
            existing_collections = [c.name for c in client.get_collections().collections]
            
            if CONVERSATIONS_COLLECTION in existing_collections:
                _qdrant_conversations = QdrantVectorStore(
                    client=client,
                    collection_name=CONVERSATIONS_COLLECTION,
                    embedding=embedding_function
                )
        except Exception as e:
            print(f"Advertencia: No se pudo inicializar la colección de conversaciones: {e}")
            _qdrant_conversations = None
    return _qdrant_conversations

class _LazyQdrantDocs:
    """Wrapper lazy para qdrant_docs que se inicializa solo cuando se accede."""
    def __init__(self):
        self._instance = None
    
    def _get_instance(self):
        if self._instance is None:
            self._instance = get_qdrant_docs()
        return self._instance
    
    def __getattr__(self, name):
        return getattr(self._get_instance(), name)
    
    def __call__(self, *args, **kwargs):
        return self._get_instance()(*args, **kwargs)

class _LazyQdrantConversations:
    """Wrapper lazy para qdrant_conversations que se inicializa solo cuando se accede."""
    def __init__(self):
        self._instance = None
        self._initialized = False
    
    def _get_instance(self):
        if not self._initialized:
            self._instance = get_qdrant_conversations()
            self._initialized = True
        return self._instance
    
    def _is_available(self):
        """Verifica si la instancia está disponible sin inicializarla si no es necesario."""
        if not self._initialized:
            # Solo inicializar cuando se necesite verificar
            self._get_instance()
        return self._instance is not None
    
    def __getattr__(self, name):
        instance = self._get_instance()
        if instance is None:
            raise AttributeError(f"'NoneType' object has no attribute '{name}'")
        return getattr(instance, name)
    
    def __call__(self, *args, **kwargs):
        instance = self._get_instance()
        if instance is None:
            return None
        return instance(*args, **kwargs)
    
    def __bool__(self):
        return self._is_available()
    
    def __repr__(self):
        if not self._initialized:
            return f"<LazyQdrantConversations (not initialized)>"
        return f"<LazyQdrantConversations (available={self._instance is not None})>"

# Variables para compatibilidad con código existente
qdrant_docs = _LazyQdrantDocs()
qdrant_conversations = _LazyQdrantConversations()
    