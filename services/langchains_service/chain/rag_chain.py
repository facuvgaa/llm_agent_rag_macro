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
llm = OllamaLLM(model="llama3.2:1b", base_url=OLLAMA_URL)

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

    cached_answer = redis_cache.get_cached_answer(question)

    if cached_answer:
        print(f"respuesta obtenida de cache: {cached_answer}")
        redis_cache.save_to_conversation(thread_id, question, cached_answer)
        return cached_answer
    
    retriever = qdrant_docs.as_retriever(search_kwargs={"k": 8})  # Más documentos para tener mejor contexto
    relevant_docs = retriever.invoke(question)
    
    print(f"🔍 Buscando documentos para: {question}")
    print(f"✅ Encontré {len(relevant_docs)} documentos relevantes")

    if relevant_docs:
        context_parts = []
        for doc in relevant_docs:
            # Intentar obtener el texto del documento
            # LangChain puede tenerlo en page_content o en metadata
            text = doc.page_content if doc.page_content else None
            
            # Si no está en page_content, buscar en metadata
            if not text and hasattr(doc, 'metadata'):
                text = doc.metadata.get('text') or doc.metadata.get('payload', {}).get('text')
            
            # Si aún no hay texto, usar el string del documento
            if not text:
                text = str(doc)
            
            if text and len(text.strip()) > 0:
                context_parts.append(text.strip())
        
        context = "\n\n---\n\n".join(context_parts)
        print(f"📄 Contexto construido con {len(context_parts)} documentos")
        print(f"📏 Longitud del contexto: {len(context)} caracteres")
        prompt = f"""sos un agente de IA que trabaja para el banco macro. Tu trabajo es responder preguntas de clientes basándote ÚNICAMENTE en la información proporcionada en el contexto.

REGLAS IMPORTANTES:
- Responde SIEMPRE basándote en el contexto proporcionado
- Si el contexto tiene información sobre tasas, plazos o cálculos, úsala para responder
- Si el contexto menciona TNA (Tasa Nominal Anual) o TEA (Tasa Efectiva Anual), úsala para hacer cálculos
- Si te preguntan por retornos o ganancias, calcula usando la información de tasas del contexto
- NO inventes información que no esté en el contexto
- Si no hay información suficiente en el contexto, di claramente: "No tengo esa información específica en los documentos disponibles"
- Sé cortés y respetuoso con el cliente
- Si hay tablas de tasas en el contexto, úsalas para responder

CONTEXTO DE DOCUMENTOS:
{context}

PREGUNTA DEL CLIENTE:
{question}

INSTRUCCIONES:
1. Revisa el contexto cuidadosamente
2. Busca información relevante sobre tasas, plazos, montos, etc.
3. Si hay suficiente información, calcula el retorno usando las tasas proporcionadas
4. Responde de forma clara y directa

RESPUESTA:"""
    else:
        print("⚠️ No se encontraron documentos relevantes, respondiendo sin contexto")
        prompt = question
    
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

