from fastapi import FastAPI 
from pydantic import BaseModel
from typing import Optional
from chain.rag_chain import generate_answer
import asyncio
from concurrent.futures import ThreadPoolExecutor

app = FastAPI(title="LangChains RAG service")

# Thread pool para ejecutar funciones síncronas sin bloquear el event loop
executor = ThreadPoolExecutor(max_workers=4)

class QueryRequest(BaseModel):
    pregunta: str
    thread_id: Optional[str] = None  # ID de conversación para mantener contexto


@app.post("/query")
async def query_rag(request: QueryRequest):
    # Ejecutar la función síncrona en un thread pool para no bloquear el event loop
    loop = asyncio.get_event_loop()
    respuesta = await loop.run_in_executor(
        executor, 
        generate_answer, 
        request.pregunta, 
        request.thread_id
    )
    return {"respuesta": respuesta}
