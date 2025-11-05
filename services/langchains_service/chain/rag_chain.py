import uuid
from langgraph.graph import START, MessagesState, StateGraph
from langgraph.checkpoint.memory import MemorySaver
from langchain_ollama.llms import OllamaLLM
from langchain_core.messages import HumanMessage, AIMessage
from models.qdrant_schemas import qdrant_docs, qdrant_conversations
from models.redis_cache import redis_cache
import os


OLLAMA_URL = "http://llm_service:11434"

# Modelo LLM
llm = OllamaLLM(model="llama3.2:3b", base_url=OLLAMA_URL)

# Grafo de estados
workflow = StateGraph(state_schema=MessagesState)

def call_model(state: MessagesState):
    # Extraer el contenido del último mensaje del usuario
    last_message = state["messages"][-1]
    # Los mensajes son objetos Message de LangChain, acceder al atributo content
    prompt = last_message.content if hasattr(last_message, 'content') else str(last_message)
    
    # Invocar el LLM con el prompt
    response = llm.invoke(prompt)
    
    # Retornar en formato de mensaje usando AIMessage de LangChain
    return {"messages": [AIMessage(content=response)]}

workflow.add_edge(START, "model")
workflow.add_node("model", call_model)

# Persistencia de memoria
memory = MemorySaver()
app = workflow.compile(checkpointer=memory)

# Función principal
def generate_answer(question: str, thread_id: str = None) -> str:
    if thread_id is None:
        thread_id = str(uuid.uuid4())

    # Obtener historial de conversación previo
    conversation_history = redis_cache.get_conversation_cache(thread_id)
    context_historico = ""
    
    if conversation_history and len(conversation_history) > 0:
        # Construir contexto histórico de las últimas 3 interacciones
        ultimas_interacciones = conversation_history[-3:]
        context_parts = []
        for msg in ultimas_interacciones:
            if msg.get("question"):
                context_parts.append(f"Pregunta anterior: {msg['question']}")
            if msg.get("answer"):
                context_parts.append(f"Respuesta anterior: {msg['answer']}")
        
        if context_parts:
            context_historico = "\n".join(context_parts)
            print(f"📜 Contexto histórico encontrado: {len(conversation_history)} mensajes previos")

    cached_answer = redis_cache.get_cached_answer(question)

    if cached_answer:
        print(f"respuesta obtenida de cache: {cached_answer}")
        redis_cache.save_to_conversation(thread_id, question, cached_answer)
        return cached_answer
    
    # Detectar saludos simples y responder directamente sin usar LLM
    question_lower = question.lower().strip()
    saludos_simples = ["hola", "hola, como estas", "como estas", "buenos días", "buenas tardes", "buenas noches", "hi", "hello"]
    
    # Respuestas directas para preguntas comunes sin contexto
    if question_lower in saludos_simples:
        answer = "Hola, ¿en qué puedo ayudarte?"
        redis_cache.cache_answer(question, answer)
        redis_cache.save_to_conversation(thread_id, question, answer)
        return answer
    
    # Si pregunta si puede buscar en internet o cosas fuera del contexto del banco
    preguntas_fuera_contexto = ["podes buscar en internet", "puedes buscar en internet", "buscar en internet", "busca en google"]
    if any(pregunta in question_lower for pregunta in preguntas_fuera_contexto):
        answer = "No, no puedo buscar en internet. Solo puedo responder con la información disponible en los documentos del banco."
        redis_cache.cache_answer(question, answer)
        redis_cache.save_to_conversation(thread_id, question, answer)
        return answer
    
    # Si pregunta si es un agente del banco
    if "agente" in question_lower and ("banco" in question_lower or "macro" in question_lower):
        answer = "Sí, soy un asistente virtual del Banco Macro. ¿En qué puedo ayudarte?"
        redis_cache.cache_answer(question, answer)
        redis_cache.save_to_conversation(thread_id, question, answer)
        return answer
    
    # Detectar preguntas específicas sobre token (trabo, bloqueado, problema, etc.)
    question_lower = question.lower().strip()
    es_pregunta_token = any(palabra in question_lower for palabra in ["token", "trabo", "traba", "bloqueado", "no funciona", "no responde", "problema con", "arreglar", "generar", "nuevo token", "crear token", "activar token"])
    
    # Detectar si menciona cambiar dispositivo/celular - esto es importante para token
    menciona_cambio_dispositivo = any(palabra in question_lower for palabra in ["cambie", "cambio", "cambiar", "nuevo celular", "nuevo dispositivo", "otro celular", "otro dispositivo"])
    
    # Detectar si pregunta específicamente sobre ir al cajero automático
    pregunta_sobre_cajero = any(palabra in question_lower for palabra in ["cajero", "quiero ir", "ir al cajero", "cajero automatico", "cajero automático", "banelco"])
    
    # Detectar preguntas vagas que necesitan contexto adicional
    preguntas_vagas = ["me podes guiar", "me guias", "como hago", "podes ayudarme", "ayudame", "guia", "instrucciones"]
    es_pregunta_vaga = any(pregunta in question_lower for pregunta in preguntas_vagas)
    
    # Si pregunta específicamente sobre ir al cajero automático, buscar información del cajero
    if pregunta_sobre_cajero:
        # Buscar específicamente sobre el proceso en el cajero automático
        # Incluir "Dirigite" que es parte del texto clave del documento
        search_query = "Dirigite cajero automatico banelco tarjeta debito claves generacion token"
        print(f"🔍 Pregunta sobre cajero automático detectada, buscando: {search_query}")
    # Si pregunta específica sobre token o cambio de dispositivo relacionado con token, mejorar la búsqueda
    elif es_pregunta_token or (menciona_cambio_dispositivo and "token" in question_lower):
        # Si la pregunta contiene "token", buscar directamente con términos clave de token
        # Usar términos específicos de activación y generación para mejorar la relevancia
        search_query = "token seguridad cajero generacion claves activacion"
        print(f"🔍 Pregunta sobre token detectada, buscando: {search_query}")
    # Si es pregunta vaga Y hay contexto histórico, usar el contexto histórico para mejorar la búsqueda
    elif es_pregunta_vaga and context_historico:
        # Extraer términos clave del contexto histórico para mejorar la búsqueda
        # Buscar palabras clave relacionadas con el tema anterior
        if "token" in context_historico.lower() or "trabo" in context_historico.lower():
            search_query = "token seguridad cajero generacion claves activacion"
        elif "tasa" in context_historico.lower() or "interes" in context_historico.lower():
            search_query = "tasa interes deposito plazo fijo"
        else:
            # Buscar con términos del contexto histórico
            search_query = question + " " + " ".join(context_historico.lower().split()[:10])
        print(f"🔍 Pregunta vaga detectada con contexto histórico, buscando: {search_query[:100]}")
    elif es_pregunta_vaga:
        # Si es pregunta vaga sin contexto, buscar con términos generales de token
        search_query = "token seguridad cajero generacion claves activacion"
        print(f"🔍 Pregunta vaga detectada sin contexto, buscando: {search_query}")
    else:
        search_query = question
    
    # Buscar documentos relevantes - aumentar k para tener más opciones
    # Para preguntas sobre cajero, buscar más documentos porque el proceso completo puede estar en documentos más abajo
    k_docs = 20 if pregunta_sobre_cajero else 8
    retriever = qdrant_docs.as_retriever(search_kwargs={"k": k_docs})
    relevant_docs = retriever.invoke(search_query)
    
    print(f"🔍 Buscando documentos para: {question}")
    print(f"✅ Encontré {len(relevant_docs)} documentos relevantes")
    
    # Mostrar preview de los primeros documentos para debugging
    if relevant_docs:
        for i, doc in enumerate(relevant_docs[:3]):
            preview = doc.page_content[:150] if hasattr(doc, 'page_content') else str(doc)[:150]
            print(f"   📄 Doc {i+1}: {preview}...")

    if relevant_docs and len(relevant_docs) > 0:
        # Filtrar documentos irrelevantes - solo usar documentos que mencionen palabras clave relacionadas
        palabras_clave_token = ["token", "cajero", "generación", "generacion", "clave", "activación", "activacion", "seguridad", "app macro", "banco macro"]
        palabras_clave_pregunta = question_lower.split()
        
        # Solo aplicar filtros estrictos para preguntas sobre ACCIONES específicas (generar, activar, crear, nuevo token)
        # NO aplicar filtros estrictos para preguntas generales (qué es, cómo funciona, para qué sirve)
        es_pregunta_accion_token = any(palabra in question_lower for palabra in ["generar", "nuevo token", "crear token", "activar token", "vencio", "venció", "como genero", "como activo", "como creo"])
        es_pregunta_general = any(palabra in question_lower for palabra in ["qué es", "que es", "como funciona", "cómo funciona", "para que", "para qué", "que es", "definicion", "definición"])
        
        context_parts = []
        for doc in relevant_docs:
            # Intentar obtener el texto del documento
            text = doc.page_content if hasattr(doc, 'page_content') and doc.page_content else None
            
            # Si no está en page_content, buscar en metadata
            if not text and hasattr(doc, 'metadata'):
                text = doc.metadata.get('text') or doc.metadata.get('payload', {}).get('text')
            
            # Si aún no hay texto, usar el string del documento
            if not text:
                text = str(doc)
            
            if text and len(text.strip()) > 0:
                text_lower = text.lower()
                
                # Filtrar documentos irrelevantes SOLO cuando es necesario
                # Para preguntas generales (qué es, cómo funciona), NO filtrar - usar todos los documentos relevantes
                if pregunta_sobre_cajero:
                    # Para preguntas sobre cajero automático, solo usar documentos que mencionen cajero automático
                    # Buscar documentos que tengan "Dirigite" o "cajero" + "banelco" o "cajero" + "tarjeta" + "claves"
                    tiene_dirigite_cajero = "dirigite" in text_lower and "cajero" in text_lower
                    tiene_cajero_banelco = "cajero" in text_lower and "banelco" in text_lower
                    tiene_cajero_tarjeta_claves = "cajero" in text_lower and ("tarjeta" in text_lower or "débito" in text_lower or "debito" in text_lower) and ("claves" in text_lower or "generación" in text_lower or "generacion" in text_lower)
                    
                    if not (tiene_dirigite_cajero or tiene_cajero_banelco or tiene_cajero_tarjeta_claves):
                        continue  # Saltar este documento si no menciona cajero automático con el proceso completo
                elif es_pregunta_accion_token and not es_pregunta_general:
                    # Solo para preguntas sobre ACCIONES específicas (generar, activar, crear), filtrar documentos que no mencionen token
                    # Para preguntas generales, NO filtrar - dejar que el modelo use todos los documentos relevantes
                    if not any(palabra in text_lower for palabra in palabras_clave_token):
                        continue  # Saltar este documento si no menciona palabras clave de token
                # Para preguntas generales, NO filtrar - usar todos los documentos recuperados
                
                # Aumentar tamaño permitido por documento para capturar más contexto
                # Pero limitar para evitar contextos demasiado largos que confundan al modelo pequeño
                context_parts.append(text.strip()[:1500])
        
        if context_parts:
            context = "\n\n---\n\n".join(context_parts)
            print(f"📄 Contexto construido con {len(context_parts)} documentos")
            print(f"📏 Longitud del contexto: {len(context)} caracteres")
            
            # Incluir contexto histórico en el prompt si existe
            contexto_completo = context
            if context_historico:
                contexto_completo = f"""CONTEXTO DE LA CONVERSACIÓN ANTERIOR:
{context_historico}

---

CONTEXTO DE DOCUMENTOS DISPONIBLES:
{context}"""
            
            # Construir prompt específico según el tipo de pregunta
            if pregunta_sobre_cajero:
                # Prompt ultra-específico para preguntas sobre cajero automático
                prompt = f"""Eres un asistente virtual del Banco Macro. El usuario pregunta específicamente sobre ir al CAJERO AUTOMÁTICO.

{contexto_completo}

PREGUNTA ACTUAL DEL CLIENTE: {question}

REGLAS ULTRA-ESTRICTAS PARA PREGUNTAS SOBRE CAJERO AUTOMÁTICO:
1. Busca en el contexto la sección que dice "Dirigite a un Cajero Automático de la red Banelco" o "2) Dirigite"
2. Si encuentras esa sección, extrae SOLO los pasos que aparezcan en esa sección específica sobre el cajero automático
3. Los pasos que DEBES mencionar (solo si están en el contexto):
   - Dirigite a un Cajero Automático de la red Banelco
   - Ingresá con tu tarjeta de débito
   - Presioná las siguientes opciones: Claves > Generación de Claves > Token de Seguridad
   - Generá la Clave de Token (un código de 6 dígitos que deberás recordar)
   - El cajero emitirá un comprobante con un Código de Activación de 8 dígitos (guarda este ticket)
4. PROHIBIDO ABSOLUTO mencionar:
   - Teléfono, llamar, 0810-555-2355
   - Sucursal, hablar con cajero, ir a sucursal
   - App, descargar, instalar, Google Play Store, App Store
   - Activar en el celular (paso 3)
   - Cualquier información sobre pagos, tasas, plazos fijos, u otros temas
5. Si el contexto menciona "1) Instalá la App Macro" o "3) Activá el Token en tu celular", IGNORA completamente esas secciones
6. Si el contexto menciona múltiples pasos numerados (1), 2), 3)), SOLO usa el paso 2) sobre el cajero automático
7. Si NO encuentras información sobre el cajero automático en el contexto, di: "No tengo información específica sobre el proceso en el cajero automático en los documentos disponibles."
8. Responde SIEMPRE en español
9. Sé claro, conciso y numera los pasos (1), 2), 3), etc.) basándote SOLO en lo que aparece en el paso del cajero automático

RESPUESTA (SOLO pasos del cajero automático extraídos del paso 2), NADA más):"""
            else:
                # Prompt general para otras preguntas - más flexible para preguntas generales
                if es_pregunta_general:
                    # Prompt más flexible para preguntas generales (qué es, cómo funciona, etc.)
                    prompt = f"""Eres un asistente virtual del Banco Macro. Responde la pregunta del cliente usando la información del contexto proporcionado.

{contexto_completo}

PREGUNTA ACTUAL DEL CLIENTE: {question}

INSTRUCCIONES:
1. Usa la información del contexto para responder la pregunta
2. Si la pregunta es sobre qué es algo o cómo funciona, puedes inferir información básica del contexto
3. Si mencionas pasos o procesos específicos, asegúrate de que estén en el contexto
4. NO inventes información sobre pasos específicos, números de teléfono, o procesos que no estén en el contexto
5. Responde SIEMPRE en español
6. Sé claro y conciso

RESPUESTA:"""
                else:
                    # Prompt más estricto para preguntas sobre acciones específicas
                    prompt = f"""Eres un asistente virtual del Banco Macro. DEBES responder SOLO usando la información que está en el contexto proporcionado. NO inventes NADA.

{contexto_completo}

PREGUNTA ACTUAL DEL CLIENTE: {question}

REGLAS ESTRICTAS (LEE CUIDADOSAMENTE):
1. ANTES de responder, verifica que CADA PASO que menciones esté EXPLÍCITAMENTE en el contexto proporcionado
2. Si la pregunta menciona "generar token", "nuevo token", "crear token", "activar token", "token vencido", "cambiar celular", "cambio de dispositivo":
   - Si el usuario YA TIENE la app instalada (dice "no me deja entrar", "ya tengo la app", "cambie de celular", "venció el token", etc.), NO menciones cómo descargar la app
   - Enfócate SOLO en los pasos de GENERACIÓN/ACTIVACIÓN del token que aparezcan en el contexto
   - Solo menciona pasos que veas en el contexto sobre: ir al CAJERO AUTOMÁTICO (no a la sucursal), generar claves, activar en el celular
   - NO inventes información sobre llamar por teléfono, ir a sucursal, o hablar con cajero a menos que esté EXPLÍCITAMENTE en el contexto
   - Si el contexto habla de "instalar app" Y "generar token", SEPARA claramente: solo menciona la parte relevante según la pregunta
3. Si la pregunta menciona "token trabo", "token bloqueado", "token no funciona":
   - Busca en el contexto información sobre "Token de Seguridad" y cómo resolver problemas
   - Si encuentras información sobre desvincular, reinstalar o reactivar el token, úsala
   - Si no encuentras información específica sobre ese problema, di qué información sí tienes disponible
4. CRÍTICO: Si un documento en el contexto habla de OTROS temas (pagos, tasas, plazos fijos, etc.) y NO menciona "token", "cajero", "generación de claves", o "activación", NO uses esa información para responder
5. Si hay contexto histórico sobre "token", úsalo para entender que el cliente ya estaba hablando del Token de Seguridad
6. Responde DIRECTAMENTE la pregunta usando SOLO la información del contexto que sea RELEVANTE
7. NO inventes pasos, procesos o información que no esté en el contexto
8. NO mezcles información de diferentes temas (pagos, tasas, etc.) con información sobre token
9. NO agregues frases como "No tengo más información" o "No sé" al final si ya diste una respuesta útil con los pasos disponibles
10. Si NO encuentras información relevante en absoluto, di: "No tengo esa información específica en los documentos disponibles."
11. Responde SIEMPRE en español
12. Sé claro, conciso y estructurado. Si hay pasos, numéralos claramente (1), 2), 3), etc.)

RESPUESTA (usa SOLO información del contexto que sea relevante a la pregunta):"""
        else:
            print("⚠️ Los documentos encontrados no tienen contenido válido")
            prompt = f"""Eres un asistente virtual del Banco Macro. 

PREGUNTA DEL CLIENTE: {question}

Si no tienes información sobre esta pregunta, responde EXACTAMENTE: "No tengo esa información específica en los documentos disponibles."

RESPUESTA:"""
    else:
        print("⚠️ No se encontraron documentos relevantes")
        prompt = f"""Eres un asistente virtual del Banco Macro. 

PREGUNTA DEL CLIENTE: {question}

No tengo información específica en los documentos disponibles para responder esta pregunta. Responde de forma breve y profesional indicando esto.

RESPUESTA:"""
    
    response = llm.invoke(prompt)
    answer = response 

    redis_cache.cache_answer(question, answer)
    
    redis_cache.save_to_conversation(thread_id, question, answer)

    try:
        if qdrant_conversations is not None and bool(qdrant_conversations):
            qdrant_conversations.add_texts([question, answer])
    except Exception as e:
        print(f"Advertencia: No se pudo guardar en Qdrant: {e}")

    return answer

