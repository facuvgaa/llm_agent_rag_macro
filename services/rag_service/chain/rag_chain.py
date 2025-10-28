import httpx
from langchain_community.vectorstores import Qdrant
from langchain_community.memory import CombinedMemory, ConversationBufferMemory, VectorStoreRetrieverMemory
from langchain_community.chains import ConversationalRetrievalChain


QDRANT_URL = "http://qdrant:6333"
EMBEDDING_SERVICE_URL = "http://embedding_service:8001/embed"  
OLLAMA_URL = "http://llm_service:8002"

class RemoteEmbeddingFunction:
    async def __call__(self, texts):
        async with httpx.AsyncClient() as client:
            response = await client.post(EMBEDDING_SERVICE_URL, json={"texts": texts})
        return response.json()["embeddings"]

embedding_function = RemoteEmbeddingFunction()



Qdrant_docs = Qdrant(
    url = QDRANT_URL,
    collection_name="docs",
    embedding_function=embedding_function)

qdrant_conversations = Qdrant(
    url=QDRANT_URL,
    collection_name="conversations",
    embedding_function=embedding_function)