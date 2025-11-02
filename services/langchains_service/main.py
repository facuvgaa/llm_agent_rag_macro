from fastapi import FastAPI 
from pydantic import BaseModel
from chain.rag_chain import generate_answer
app = FastAPI(title="LangChains RAG service")

class QueryRequest(BaseModel):
    pregunta: str


@app.post("/query")
def query_rag(request: QueryRequest):
    respuesta = generate_answer(request.pregunta)
    return {"respuesta": respuesta}
