from fastapi import FastAPI
from routes.routes import router as rag_router

app = FastAPI(
    title="Macro-Flow API Gateway",
    description="API Gateway para orquestar servicios RAG",
    version="1.0.0"
)

app.include_router(rag_router, prefix="/rag", tags=["RAG"])