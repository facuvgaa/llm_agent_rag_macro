from fastapi import FastAPI, APIRouter, WebSocket, WebSocketDisconnect, routing
import httpx

router = APIRouter()

app = FastAPI(
    title="Macro-Flow API Gateway",
    description="API Gateway para orquestar servicios RAG",
    version="1.0.0"
)


RAG_SERVICE_URL = "http://rag_service:8000/query"

@router.get("/")
async def queryrag(payload: dict):
    async with httpx.AsyncClient() as client:
        response = await client.post(RAG_SERVICE_URL, json=payload)
        return response.json()
    
@router.websocket("/chat")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    await websocket.send_text("🤖 Conexión establecida con el RAG Gateway.")
    try:
        while True:
            data = await websocket.receive_text()

            async with httpx.AsyncClient() as client:
                response = await client.post(RAG_SERVICE_URL, json={"pregunta": data})
                
            respuesta = response.json().get("respuesta", "no obtuvo respuesta del rag")
            await websocket.send_text(respuesta)

    except WebSocketDisconnect:
        print("❌ Cliente desconectado del WebSocket")