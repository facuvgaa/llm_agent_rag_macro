# 📊 Informe Técnico: Macro RAG - Análisis Profundo del Proyecto

## 📋 Tabla de Contenidos
1. [Visión General de Arquitectura](#visión-general-de-arquitectura)
2. [Flujos Funcionales](#flujos-funcionales)
3. [Detección de Bugs Críticos](#detección-de-bugs-críticos)
4. [Mejoras Técnicas Recomendadas](#mejoras-técnicas-recomendadas)
5. [Plan de Refactor Priorizado](#plan-de-refactor-priorizado)
6. [Arquitectura Detallada de Servicios](#arquitectura-detallada-de-servicios)

---

## 🏗️ Visión General de Arquitectura

### Stack ETL (infra/docker-compose.etl.yml)

**Servicios:**
- **Airflow**: Orquesta el pipeline de procesamiento de documentos
- **Kafka**: Sistema de mensajería para eventos ETL
- **Qdrant**: Base de datos vectorial para embeddings
- **Redis**: Cache para evitar reprocesamiento de URLs
- **Controller Service**: Consume eventos de Kafka y orquesta la segunda fase

**Flujo ETL:**
```
URLs → Airflow DAG → Chunking PDFs → Generación Embeddings → Carga Qdrant → Evento Kafka
```

### Stack RAG (infra/docker-compose.rag.yml)

**Servicios:**
- **Gateway Service**: Punto de entrada para usuarios (FastAPI)
- **LangChains Service**: Orquestador de RAG con LangGraph
- **Embedding Service**: Generación de embeddings (SentenceTransformers)
- **LLM Service**: Servicio Ollama con modelo llama3.2:1b
- **Qdrant**: Base de datos vectorial para búsqueda semántica
- **Redis**: ✅ Cache de respuestas e historial de conversaciones (implementado)

**Flujo RAG (Intención):**
```
Usuario → API Gateway → LangChains → Embedding Service → Qdrant → LLM → Respuesta
```

---

## 🔄 Flujos Funcionales

### 1. Pipeline ETL de Documentos (Airflow)

**Archivo:** `services/airflow_dags/chunk_and_embedding.py`

**Etapas:**
1. **Lectura de URLs**: Lee desde `urls.txt`
2. **Deduplicación**: Usa Redis para evitar reprocesar PDFs ya procesados
3. **Chunking**: Convierte PDFs a Parquet con chunks de texto
4. **Generación Embeddings**: Transforma chunks a vectores
5. **Carga Qdrant**: Almacena embeddings en base de datos vectorial
6. **Notificación**: Publica evento `etl_done` en Kafka

**Dependencias Externas:**
- `pdf_chunk_flow`: MacroEtlPdfChunks (NO presente en repo)
- `embedding_flow.transform.transform`: transform_embedding (NO presente en repo)
- `embedding_flow.load.load`: load_embedding (NO presente en repo)

⚠️ **Riesgo Alto**: Si estos módulos no están en la imagen Docker o como plugins, el DAG fallará.

### 2. Orquestación Post-ETL (Controller Service)

**Archivo:** `services/controller_service/app/main.py`

**Proceso:**
1. Escucha mensajes de Kafka en topic `etl-events`
2. Al recibir `{"event": "etl_done"}`, intenta notificar al gateway
3. Actualmente solo loguea instrucciones manuales para cambiar al stack RAG

**Bug:** Llama a `/start` que no existe en el gateway.

### 3. API Gateway

**Archivo:** `services/api_gateway/app/app.py` y `services/api_gateway/app/routes/routes.py`

**Endpoints:**
- `GET /rag/`: Proxy a servicio RAG (incorrecto, debería ser POST)
- `WebSocket /rag/chat`: Chat en tiempo real

**Bugs Detectados:**
- Import incorrecto de router
- URL apunta a servicio inexistente (`rag_service:8000`)
- GET endpoint acepta body (antipatrón)

### 4. Servicio LangChains/RAG

**Archivo:** `services/langchains_service/main.py` y `services/langchains_service/chain/rag_chain.py`

**Funcionalidad:**
- Expone `POST /query` con `{"pregunta": "..."}`
- Usa LangGraph para orquestar LLM
- Guarda conversaciones en Qdrant (si colección existe)

**⚠️ Problema Crítico**: **NO implementa RAG real**
- No recupera documentos de Qdrant
- No construye contexto con documentos relevantes
- Solo llama al LLM directamente (conversational, no RAG)

**Configuración Qdrant:**
- `DOCS_COLLECTION`: "embeddings_collection" (documentos ETL)
- `CONVERSATIONS_COLLECTION`: "conversations" (opcional)
- Embedding remoto via `embedding_service:8001/embedding`

### 5. Servicio de Embeddings

**Archivo:** `services/embedding_service/app/main.py`

**Funcionalidad:**
- Endpoint: `POST /embedding`
- Modelo: `sentence-transformers/all-mpnet-base-v2`
- Retorna: Lista de vectores (768 dimensiones)

**Limitaciones:**
- Sin validación de tamaño de entrada
- Sin rate limiting
- Sin endpoints de healthcheck

---

## 🐛 Detección de Bugs Críticos

### 🔴 Bugs Críticos que Rompen Funcionalidad

#### 1. API Gateway - Import y Registro de Router Incorrecto
**Archivo:** `services/api_gateway/app/app.py`
```python
from routes.routes import queryrag as rag_router  # ❌ queryrag es función, no router
app.include_router(rag_router, ...)  # ❌ Fallará
```

**Solución:**
```python
from routes.routes import router as rag_router
app.include_router(rag_router, prefix="/rag", tags=["RAG"])
```

#### 2. API Gateway - URL de Servicio Incorrecta
**Archivo:** `services/api_gateway/app/routes/routes.py`
```python
RAG_SERVICE_URL = "http://rag_service:8000/query"  # ❌ Servicio no existe
```

**Realidad:**
- Servicio correcto: `langchains_service` (puerto 8002)
- Debe ser: `http://langchains_service:8002/query`

#### 3. API Gateway - Endpoint GET con Body
**Archivo:** `services/api_gateway/app/routes/routes.py`
```python
@router.get("/")  # ❌ GET no debe aceptar body
async def queryrag(payload: dict):
```

**Solución:** Cambiar a POST con schema Pydantic:
```python
@router.post("/")
async def queryrag(request: QueryRequest):
```

#### 4. LangChains Service - NO Implementa RAG Real
**Archivo:** `services/langchains_service/chain/rag_chain.py`

**Problema:** Falta recuperación de documentos relevantes de Qdrant antes de llamar al LLM.

**Solución Requerida:**
```python
# Agregar retriever
retriever = qdrant_docs.as_retriever(search_kwargs={"k": 4})
docs = retriever.invoke(question)

# Construir prompt con contexto
context = "\n".join([doc.page_content for doc in docs])
prompt = f"Contexto: {context}\n\nPregunta: {question}"
```

#### 5. Docker Compose - Configuración de Env Incorrecta
**Archivo:** `infra/docker-compose.rag.yml`
```yaml
environment:
  - ../environment_variables/.env.rag  # ❌ Debe ser env_file
```

**Solución:**
```yaml
env_file:
  - ../environment_variables/.env.rag
```

#### 6. Controller Service - Endpoint Inexistente
**Archivo:** `services/controller_service/app/controller.py`
```python
gateway_url = "http://gateway_service:8000/start"  # ❌ No existe
```

**Solución:** Crear endpoint `/start` en gateway o cambiar a endpoint existente.

#### 7. Airflow DAG - Variable de Entorno Inconsistente
**Archivo:** `services/airflow_dags/chunk_and_embedding.py`
```python
KAFKA_BROKER = os.getenv("KAFKA_BROKER", ...)  # ❌ Variable no definida en compose
```

**En docker-compose.etl.yml se define:**
```yaml
KAFKA_BOOTSTRAP_SERVERS: kafka_service:9092
```

**Solución:** Alinear nombres de variables.

### 🟡 Bugs Menores y Mejoras

#### 8. Embedding Service - Sin Validación de Input
- Sin límites de tamaño de batch
- Riesgo de OOM con lotes grandes

#### 9. Qdrant Schemas - Falta Validación de Respuesta
**Archivo:** `services/langchains_service/models/qdrant_schemas.py`
```python
return response.json()[0]  # ❌ Asume estructura exacta
```

**Solución:** Validar estructura y manejar errores.

#### 10. Falta de Timeouts y Retries
- `httpx.AsyncClient()` sin timeout configurado
- Sin retry logic en llamadas HTTP
- Riesgo de cuelgues en servicios lentos

#### 11. Configuración Dispersa
- `core/config.py` está vacío
- Constantes hardcodeadas en múltiples archivos
- Falta uso de `pydantic-settings`

#### 12. Versiones de Dependencias
**Archivo:** `services/langchains_service/requirements.txt`
```
langchain==1.0.2  # ❌ Versión incorrecta (langchain core es 0.x)
```

#### 13. Sin Healthchecks
- Ningún servicio expone `/health`
- Docker healthchecks básicos solo en `llm_service`

#### 14. Logging Inconsistente
- Algunos servicios usan `logging`, otros `print`
- Sin formato estándar
- Falta de niveles apropiados

---

## 🔧 Mejoras Técnicas Recomendadas

### 1. Arquitectura y Contratos entre Servicios

**Problemas:**
- Nombres de servicios inconsistentes entre compose files
- URLs hardcodeadas
- Falta de service discovery

**Soluciones:**
- Usar variables de entorno para todas las URLs
- Implementar service discovery o usar nombres de Docker consistentes
- Documentar contratos de API entre servicios

### 2. Implementación Real de RAG

**Estado Actual:**
- LangChains solo llama al LLM sin contexto de documentos

**Mejora Requerida:**
```python
# En rag_chain.py
def generate_answer(question: str, thread_id: str = None) -> str:
    # 1. Recuperar documentos relevantes
    retriever = qdrant_docs.as_retriever(search_kwargs={"k": 4})
    relevant_docs = retriever.invoke(question)
    
    # 2. Construir contexto
    context = "\n\n".join([doc.page_content for doc in relevant_docs])
    
    # 3. Construir prompt con contexto
    prompt = f"""Basándote en el siguiente contexto, responde la pregunta.
    
Contexto:
{context}

Pregunta: {question}

Respuesta:"""
    
    # 4. Llamar LLM con prompt enriquecido
    result = app.invoke({"messages": [{"role": "user", "content": prompt}]}, ...)
```

### 3. Configuración Centralizada

**Crear:** `services/langchains_service/core/config.py`
```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    qdrant_url: str = "http://qdrant:6333"
    qdrant_api_key: str
    embedding_service_url: str = "http://embedding_service:8001/embedding"
    ollama_url: str = "http://llm_service:11434"
    ollama_model: str = "llama3.2:1b"
    docs_collection: str = "embeddings_collection"
    conversations_collection: str = "conversations"
    
    class Config:
        env_file = ".env"
```

### 4. Manejo de Errores y Resiliencia

**Mejoras:**
- Timeouts en todas las llamadas HTTP
- Retry logic con backoff exponencial
- Circuit breakers para servicios externos
- Fallbacks graceful cuando servicios no están disponibles

**Ejemplo:**
```python
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
async def call_embedding_service(texts: list[str]):
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            EMBEDDING_SERVICE_URL,
            json={"texts": texts},
            timeout=30.0
        )
        response.raise_for_status()
        return response.json()
```

### 5. Validación de Inputs

**Embedding Service:**
```python
from pydantic import BaseModel, Field, validator

class EmbeddingRequest(BaseModel):
    texts: list[str] = Field(..., min_items=1, max_items=100)
    
    @validator('texts')
    def validate_texts(cls, v):
        total_chars = sum(len(t) for t in v)
        if total_chars > 100000:  # Límite razonable
            raise ValueError("Batch demasiado grande")
        return v
```

### 6. Observabilidad

**Implementar:**
- Endpoints `/health` y `/ready` en todos los servicios
- Métricas Prometheus básicas
- Trazas OpenTelemetry para debugging
- Logging estructurado con niveles apropiados

**Ejemplo Healthcheck:**
```python
@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.get("/ready")
async def ready():
    # Verificar conexión a Qdrant
    try:
        client.get_collections()
        return {"status": "ready"}
    except Exception:
        return {"status": "not ready"}, 503
```

### 7. Seguridad

**Mejoras:**
- CORS configurado apropiadamente
- Rate limiting en endpoints públicos
- Validación de inputs más estricta
- Secrets management (no hardcodear API keys)

### 8. Testing

**Actual:** Sin tests

**Recomendado:**
- Unit tests para lógica de negocio
- Integration tests para contratos entre servicios
- Tests end-to-end para flujos completos

---

## 📝 Plan de Refactor Priorizado

### Fase 1: Correcciones Críticas (Bloquean Funcionalidad)

**Prioridad:** 🔴 ALTA

1. **Corregir API Gateway**
   - Arreglar import de router
   - Cambiar GET a POST con schema
   - Corregir URL a `langchains_service:8002`

2. **Corregir Docker Compose RAG**
   - Cambiar `environment` a `env_file` en langchains_service

3. **Implementar RAG Real**
   - Agregar retriever de Qdrant en `rag_chain.py`
   - Construir prompts con contexto de documentos

4. **Alinear Variables de Entorno**
   - Unificar `KAFKA_BROKER` / `KAFKA_BOOTSTRAP_SERVERS`
   - Documentar todas las variables requeridas

### Fase 2: Mejoras de Infraestructura

**Prioridad:** 🟡 MEDIA

5. **Configuración Centralizada**
   - Crear `core/config.py` con pydantic-settings
   - Migrar todas las constantes hardcodeadas

6. **Healthchecks y Observabilidad**
   - Agregar `/health` en todos los servicios
   - Configurar healthchecks en Docker Compose
   - Implementar logging estructurado

7. **Manejo de Errores**
   - Agregar timeouts a todas las llamadas HTTP
   - Implementar retry logic
   - Agregar validación de inputs

### Fase 3: Optimizaciones y Mejoras

**Prioridad:** 🟢 BAJA

8. **Validación y Rate Limiting**
   - Validar tamaños de batch en embedding service
   - Implementar rate limiting básico

9. **Documentación**
   - Documentar APIs con OpenAPI/Swagger
   - Crear diagramas de arquitectura actualizados
   - Documentar variables de entorno

10. **Testing**
    - Agregar tests unitarios básicos
    - Tests de integración para contratos

---

## 🏛️ Arquitectura Detallada de Servicios

### API Gateway (`services/api_gateway/`)

**Stack:** FastAPI + uvicorn

**Responsabilidades:**
- Punto de entrada único para clientes
- Enrutamiento a servicios backend
- WebSocket para chat en tiempo real

**Endpoints Actuales:**
- `GET /rag/` - Query RAG (incorrecto, debe ser POST)
- `WebSocket /rag/chat` - Chat WebSocket

**Dependencias:**
- `langchains_service:8002`

### LangChains Service (`services/langchains_service/`)

**Stack:** FastAPI + LangGraph + LangChain + Ollama

**Responsabilidades:**
- Orquestar flujo RAG completo
- Gestionar estado de conversaciones
- Integrar LLM con recuperación de documentos

**Endpoints:**
- `POST /query` - Query con pregunta

**Dependencias:**
- `embedding_service:8001` - Generación de embeddings
- `qdrant:6333` - Base de datos vectorial
- `llm_service:11434` - LLM (Ollama)
- `redis_service:6379` - Cache de respuestas e historial de conversaciones

**Estado Actual:** No implementa RAG real (falta retrieval)

### Embedding Service (`services/embedding_service/`)

**Stack:** FastAPI + SentenceTransformers

**Responsabilidades:**
- Generar embeddings de texto
- Modelo: `all-mpnet-base-v2` (768 dimensiones)

**Endpoints:**
- `POST /embedding` - Generar embeddings de lista de textos

**Limitaciones:**
- Sin validación de tamaño
- Sin rate limiting

### LLM Service (`docker/llm_service/`)

**Stack:** Ollama

**Modelo:** `llama3.2:1b`

**Responsabilidades:**
- Generar respuestas basadas en prompts
- Exponer API compatible con LangChain Ollama

### Controller Service (`services/controller_service/`)

**Stack:** Kafka Consumer + Docker Client

**Responsabilidades:**
- Consumir eventos de Kafka
- Orquestar transición ETL → RAG
- Actualmente solo notifica (no automatiza)

**Eventos Escuchados:**
- `{"event": "etl_done"}` - ETL completado

### Airflow DAG (`services/airflow_dags/`)

**Stack:** Apache Airflow + Confluent Kafka

**DAG:** `chunkear_and_embedding`

**Responsabilidades:**
- Ejecutar pipeline ETL de documentos
- Chunking, embedding, carga a Qdrant
- Publicar eventos en Kafka

**Dependencias Externas (No en repo):**
- `pdf_chunk_flow`
- `embedding_flow.transform.transform`
- `embedding_flow.load.load`

### Qdrant

**Stack:** Qdrant Vector DB

**Colecciones:**
- `embeddings_collection` - Documentos procesados por ETL
- `conversations` (opcional) - Historial de conversaciones

### Redis

**Uso en ETL:**
- Cache de URLs procesadas (set `processed_urls`)

**Uso en RAG:**
- ✅ **IMPLEMENTADO**: Cache de respuestas para preguntas frecuentes
  - Cache automático de preguntas/respuestas con TTL configurable (default: 1 hora)
  - Clave generada con hash SHA256 de la pregunta normalizada
  - Ubicación: `services/langchains_service/models/redis_cache.py`
- ✅ **IMPLEMENTADO**: Historial de conversaciones por `thread_id`
  - Almacena hasta 50 mensajes por conversación
  - Expiración automática después de 7 días
  - Formato: `conversation:{thread_id}` como lista Redis

---

## 🔍 Análisis de Dependencias

### Dependencias Faltantes en Repositorio

**Críticas para ETL:**
- `pdf_chunk_flow` - MacroEtlPdfChunks
- `embedding_flow.transform.transform` - transform_embedding
- `embedding_flow.load.load` - load_embedding

**Solución:** Deben estar como:
- Plugins de Airflow en `services/airflow_dags/plugins/`
- O incluidas en la imagen Docker de Airflow

### Variables de Entorno Requeridas

**ETL Stack:**
- `QDRANT_URL`
- `QDRANT_API_KEY`
- `KAFKA_BOOTSTRAP_SERVERS`
- `REDIS_HOST`, `REDIS_PORT`

**RAG Stack:**
- `QDRANT_URL`
- `QDRANT_API_KEY`
- `QDRANT_COLLECTION_DOCS`
- `QDRANT_COLLECTION_CONVERSATIONS`
- `EMBEDDING_SERVICE_URL`
- `OLLAMA_URL`

**Recomendación:** Crear `.env.example` con todas las variables documentadas.

---

## 📊 Resumen Ejecutivo

### Estado Actual
- ✅ Arquitectura bien diseñada conceptualmente
- ✅ Separación de servicios apropiada
- ⚠️ Bugs críticos que bloquean funcionalidad
- ❌ RAG no implementado correctamente
- ❌ Falta de tests y validaciones

### Bugs Críticos Identificados: 7
1. Import/registro de router incorrecto
2. URL de servicio RAG incorrecta
3. Endpoint GET con body
4. RAG no implementado (solo LLM)
5. Configuración env incorrecta en compose
6. Endpoint inexistente en controller
7. Variables de entorno inconsistentes

### Mejoras Recomendadas: 14
- Configuración centralizada
- Healthchecks y observabilidad
- Manejo de errores robusto
- Validación de inputs
- Rate limiting
- Testing
- Documentación

### Esfuerzo Estimado de Refactor
- **Fase 1 (Crítico):** 1-2 días
- **Fase 2 (Infraestructura):** 3-5 días
- **Fase 3 (Optimizaciones):** 5-7 días

**Total:** ~2 semanas para refactor completo

---

## 🚀 Quick Start (Después de Correcciones)

### Levantar Stack ETL
```bash
make etl-up
# Acceder a Airflow: http://localhost:8080
```

### Levantar Stack RAG
```bash
make rag-up
# Gateway: http://localhost:8000
# LangChains: http://localhost:8002
```

### Probar RAG (WebSocket)
```javascript
const ws = new WebSocket('ws://localhost:8000/rag/chat');
ws.send('¿Qué información tienes disponible?');
```

---

**Última Actualización:** Enero 2025  
**Versión del Análisis:** 1.0

