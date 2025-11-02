from fastapi import FastAPI
from pydantic import BaseModel
from app.model.embedder import get_embeddings

app = FastAPI(title="embedding service 768 dimentions")

class EmbeddingRequest(BaseModel):
    texts: list[str]



@app.post("/embedding")
def embeded_text(requests: EmbeddingRequest):
    embedding = get_embeddings(requests.texts)
    return embedding