from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
import httpx

router = APIRouter()

RAG_SERVICE_URL = "http://langchains_service:8000/query"

@router.post("/")
async def queryrag(payload: dict):
    try:
        # Asegurar que el payload tenga el formato correcto
        request_payload = {
            "pregunta": payload.get("pregunta", ""),
            "thread_id": payload.get("thread_id", None)  # Pasar thread_id si existe
        }
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(RAG_SERVICE_URL, json=request_payload)
            response.raise_for_status()  # Lanza excepción si status >= 400
            
            # Verificar si la respuesta es JSON válido
            try:
                return response.json()
            except ValueError as e:
                # Si no es JSON, devolver el texto de error
                raise HTTPException(
                    status_code=502,
                    detail=f"Respuesta inválida del servicio RAG: {response.text[:200]}"
                )
                
    except httpx.ConnectError:
        raise HTTPException(
            status_code=503,
            detail="Servicio RAG no disponible. Verifique que langchains_service esté corriendo."
        )
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=504,
            detail="Timeout esperando respuesta del servicio RAG (120s). El servicio puede estar sobrecargado o procesando una consulta compleja."
        )
    except httpx.HTTPStatusError as e:
        # Si el servicio devuelve un error HTTP
        try:
            error_detail = e.response.json()
        except:
            error_detail = e.response.text[:200]
        
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"Error del servicio RAG: {error_detail}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error interno: {str(e)}"
        )
    
@router.websocket("/chat")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    await websocket.send_text("🤖 Conexión establecida con el RAG Gateway.")
    try:
        while True:
            data = await websocket.receive_text()

            try:
                async with httpx.AsyncClient(timeout=120.0) as client:
                    response = await client.post(RAG_SERVICE_URL, json={"pregunta": data})
                    response.raise_for_status()
                    
                    try:
                        respuesta = response.json().get("respuesta", "No se obtuvo respuesta del servidor")
                    except ValueError:
                        respuesta = f"Error: {response.text[:200]}"
                    
                    await websocket.send_text(respuesta)
            except httpx.ConnectError:
                await websocket.send_text("❌ Error: Servicio RAG no disponible")
            except httpx.TimeoutException:
                await websocket.send_text("❌ Error: Timeout esperando respuesta (120s)")
            except httpx.HTTPStatusError as e:
                await websocket.send_text(f"❌ Error {e.response.status_code}: {e.response.text[:200]}")
            except Exception as e:
                await websocket.send_text(f"❌ Error: {str(e)}")

    except WebSocketDisconnect:
        print("❌ Cliente desconectado del WebSocket")