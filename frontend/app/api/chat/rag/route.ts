import { ChatSettings } from "@/types"
import { StreamingTextResponse } from "ai"
import { ServerRuntime } from "next"

export const runtime: ServerRuntime = "edge"

// URL de nuestro API Gateway RAG
const RAG_API_URL = process.env.NEXT_PUBLIC_RAG_API_URL || "http://localhost:8000/rag"

export async function POST(request: Request) {
  const json = await request.json()
  const { chatSettings, messages } = json as {
    chatSettings: ChatSettings
    messages: any[]
  }

  try {
    // Obtener el último mensaje del usuario (el más reciente que no sea del sistema)
    const userMessages = messages.filter((msg: any) => msg.role === "user")
    const lastUserMessage = userMessages[userMessages.length - 1]
    
    if (!lastUserMessage) {
      throw new Error("No user message found")
    }

    // Extraer thread_id del chat_id del primer mensaje si existe
    // Usamos el chat_id como thread_id para mantener el contexto de conversación
    const threadId = messages.length > 0 && messages[0].chat_id 
      ? messages[0].chat_id 
      : null
    
    // Preparar payload para nuestro API Gateway
    const payload: any = {
      pregunta: lastUserMessage.content
    }
    
    if (threadId) {
      payload.thread_id = threadId
    }

    console.log(`[RAG API] Enviando pregunta: ${lastUserMessage.content.substring(0, 50)}...`)

    // Llamar a nuestro API Gateway
    const response = await fetch(RAG_API_URL, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    })

    if (!response.ok) {
      const errorText = await response.text()
      throw new Error(`API Gateway error (${response.status}): ${errorText}`)
    }

    const data = await response.json()
    const respuesta = data.respuesta || data.message || "No se obtuvo respuesta"

    console.log(`[RAG API] Respuesta recibida: ${respuesta.substring(0, 50)}...`)

    // Crear un stream de texto simple compatible con StreamingTextResponse
    // Dividir la respuesta en chunks pequeños para simular streaming
    const stream = new ReadableStream({
      async start(controller) {
        const encoder = new TextEncoder()
        
        // Dividir la respuesta en palabras y enviarlas en chunks pequeños
        const words = respuesta.split(" ")
        
        for (let i = 0; i < words.length; i++) {
          const chunk = words[i] + (i < words.length - 1 ? " " : "")
          
          // Enviar el chunk como texto plano (StreamingTextResponse se encarga del formato)
          controller.enqueue(encoder.encode(chunk))
          
          // Pequeña pausa para simular streaming real
          await new Promise((resolve) => setTimeout(resolve, 30))
        }
        
        controller.close()
      },
    })

    // Usar StreamingTextResponse que formatea correctamente el stream
    return new StreamingTextResponse(stream)
  } catch (error: any) {
    console.error("[RAG API] Error:", error)
    const errorMessage = error.message || "Error al conectar con el API Gateway RAG"
    const errorCode = error.status || 500

    return new Response(JSON.stringify({ message: errorMessage }), {
      status: errorCode,
      headers: {
        "Content-Type": "application/json",
      },
    })
  }
}

