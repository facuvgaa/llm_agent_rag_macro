from fastapi import FastAPI 
from pydantic import BaseModel
from chain.rag_chain import generar_pregunta


app = FastAPI(title="RAG service")

class queryRequest(BaseModel):
    pregunta : str


@app.post("/query")
async def query_rag(request :queryRequest ):
    pregunta = await generar_pregunta(request.pregunta)
    return {"pregunta":pregunta}
