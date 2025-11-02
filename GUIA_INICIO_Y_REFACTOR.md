# 🚀 Guía de Inicio y Plan de Refactor - Macro RAG

## 📚 Índice
1. [Guía de Inicio para Desarrollador Junior](#guía-de-inicio-para-desarrollador-junior)
2. [Plan de Refactor con DDD Architect](#plan-de-refactor-con-ddd-architect)
3. [Glosario de Términos](#glosario-de-términos)

---

## 🎯 Guía de Inicio para Desarrollador Junior

### ¿Qué es este proyecto?

**Macro RAG** es un sistema que permite hacer preguntas sobre documentos PDF usando Inteligencia Artificial. Tiene dos partes principales:

1. **ETL (Extract, Transform, Load)**: Procesa PDFs, los convierte en texto, genera "embeddings" (representaciones numéricas) y los guarda
2. **RAG (Retrieval Augmented Generation)**: Permite hacer preguntas sobre esos documentos usando un modelo de lenguaje

### 🛠️ Prerequisitos

Antes de empezar, necesitas tener instalado:

```bash
# Verificar que tienes Docker y Docker Compose
docker --version
docker compose version

# Si no los tienes, instálalos según tu sistema operativo
# Linux: sudo apt-get install docker.io docker-compose
```

### 📦 Paso 1: Preparar el Entorno

1. **Clonar o navegar al proyecto**:
```bash
cd /home/facuvega/Documentos/agent-full
```

2. **Crear archivos de entorno necesarios**:
```bash
# Crear directorio si no existe
mkdir -p environment_variables

# Crear archivo para Qdrant
cat > environment_variables/.env.qdrant << EOF
QDRANT__SERVICE__GRPC_PORT=6334
QDRANT_API_KEY=dev_key_123
EOF

# Crear archivo para RAG
cat > environment_variables/.env.rag << EOF
QDRANT_URL=http://qdrant_service:6333
QDRANT_API_KEY=dev_key_123
DOCS_COLLECTION=embeddings_collection
CONVERSATIONS_COLLECTION=conversations
EMBEDDING_SERVICE_URL=http://embedding_service:8001/embedding
OLLAMA_URL=http://llm_service:11434
OLLAMA_MODEL=llama3.2:1b
EOF
```

### 🏃 Paso 2: Levantar el Stack ETL (Para procesar documentos)

```bash
# Levantar servicios ETL (Airflow, Kafka, Qdrant, Redis)
make etl-up

# O manualmente:
docker compose -f infra/docker-compose.etl.yml up -d
```

**Espera unos minutos** para que los servicios inicien. Luego verifica:

```bash
# Ver estado de contenedores
docker ps

# Deberías ver:
# - airflow_service (puerto 8080)
# - kafka_service
# - qdrant_service (puertos 6333, 6334)
# - redis (puerto 6379)
```

**Acceder a Airflow**:
- Abre tu navegador: http://localhost:8080
- Usuario: `airflow`
- Contraseña: `airflow`

### 🔍 Paso 3: Levantar el Stack RAG (Para hacer preguntas)

```bash
# Levantar servicios RAG (Gateway, LangChains, Embedding, LLM)
make rag-up

# O manualmente:
docker compose -f infra/docker-compose.rag.yml up -d
```

**Verificar servicios**:
```bash
docker ps

# Deberías ver:
# - gateway_service (puerto 8000)
# - langchains_service (puerto 8002)
# - embedding_service (puerto 8001)
# - llm_service (puerto 11434)
# - qdrant_service
# - redis_service
```

### 🧪 Paso 4: Probar el Sistema

**Opción 1: Probar API Gateway directamente**:
```bash
# El endpoint debería funcionar así (aunque tiene bugs actualmente)
curl -X POST http://localhost:8000/rag/ \
  -H "Content-Type: application/json" \
  -d '{"pregunta": "¿Qué documentos tienes disponibles?"}'
```

**Opción 2: Probar LangChains Service directamente**:
```bash
curl -X POST http://localhost:8002/query \
  -H "Content-Type: application/json" \
  -d '{"pregunta": "Hola"}'
```

### 🐛 Problemas Comunes

1. **Error: "No such file or directory" en env_file**
   - Solución: Verifica que existan los archivos `.env.qdrant` y `.env.rag` en `environment_variables/`

2. **Error: "Connection refused"**
   - Solución: Espera unos minutos más, algunos servicios tardan en iniciar. Verifica con `docker ps` que todos estén corriendo.

3. **Error: "Port already in use"**
   - Solución: Detén otros contenedores que usen esos puertos:
   ```bash
   docker compose -f infra/docker-compose.etl.yml down
   docker compose -f infra/docker-compose.rag.yml down
   ```

### 📋 Comandos Útiles

```bash
# Ver logs de un servicio específico
docker logs gateway_service
docker logs langchains_service

# Ver logs en tiempo real
docker logs -f gateway_service

# Detener todo
make etl-down
docker compose -f infra/docker-compose.rag.yml down

# Limpiar volúmenes (CUIDADO: borra datos)
docker compose -f infra/docker-compose.rag.yml down -v
```

---

## 🏗️ Plan de Refactor con DDD Architect

### 🎯 Filosofía del Refactor

Vamos a aplicar **Domain-Driven Design (DDD)** y **Arquitectura Hexagonal** para:
- Separar lógica de negocio de infraestructura
- Hacer el código más testeable y mantenible
- Facilitar la colaboración entre desarrolladores

### 📐 Arquitectura Propuesta (DDD + Hexagonal)

```
services/
├── {bounded_context}/
│   ├── domain/              # Lógica de negocio pura
│   │   ├── entities/        # Entidades del dominio
│   │   ├── value_objects/   # Objetos de valor
│   │   ├── services/        # Servicios de dominio
│   │   └── repositories/    # Interfaces (contratos)
│   ├── application/         # Casos de uso (orquestación)
│   │   ├── use_cases/
│   │   ├── dto/
│   │   └── mappers/
│   ├── infrastructure/      # Implementaciones técnicas
│   │   ├── adapters/
│   │   ├── repositories/
│   │   ├── clients/
│   │   └── config/
│   └── presentation/        # API/FastAPI
│       ├── routes/
│       ├── schemas/
│       └── middleware/
```

---

## 📅 Plan de Refactor - Fases Detalladas

### 🔴 FASE 0: Preparación y Alineación (Día 1)

**Objetivo**: Alinear equipo, entender dominio, definir bounded contexts

#### Tareas con Senior Architect:

1. **Sesión de Domain Discovery** (2-3 horas)
   - Identificar **Bounded Contexts**:
     - `etl` (Extract, Transform, Load)
     - `retrieval` (Búsqueda de documentos)
     - `generation` (Generación de respuestas)
     - `conversation` (Gestión de conversaciones)
   - Identificar **Agregados**:
     - `Document` (entidad raíz del ETL)
     - `Query` (consulta del usuario)
     - `Conversation` (sesión de chat)
   - Definir **Value Objects**:
     - `EmbeddingVector`, `DocumentChunk`, `QueryText`

2. **Crear Documento de Arquitectura** (1 hora)
   - Diagrama de contextos
   - Contratos entre servicios
   - Diccionario de dominio

**Entregables**:
- `docs/architecture/ddd-contexts.md`
- `docs/architecture/service-contracts.md`

---

### 🔴 FASE 1: Correcciones Críticas (Días 2-3)

**Objetivo**: Hacer funcionar el sistema básico

#### 1.1 Corregir API Gateway (2 horas)

**Tarea para Junior (con supervisión)**:
- [ ] Crear `services/api_gateway/app/presentation/routes/rag_routes.py`
- [ ] Corregir import del router
- [ ] Cambiar GET a POST con schema Pydantic
- [ ] Corregir URL del servicio backend

**Archivos a modificar**:
- `services/api_gateway/app/app.py`
- `services/api_gateway/app/routes/routes.py` (refactorizar)

**Código de referencia**:
```python
# Nueva estructura sugerida
# services/api_gateway/app/presentation/schemas/rag_schemas.py
from pydantic import BaseModel

class RAGQueryRequest(BaseModel):
    pregunta: str
    thread_id: str | None = None

class RAGQueryResponse(BaseModel):
    respuesta: str
    sources: list[str] = []
```

#### 1.2 Corregir Docker Compose RAG (30 minutos)

**Tarea para Junior**:
- [ ] Cambiar `environment` a `env_file` en `langchains_service`
- [ ] Verificar que todas las variables estén en `.env.rag`

**Archivo**: `infra/docker-compose.rag.yml`

#### 1.3 Implementar RAG Real (4 horas)

**Tarea para Junior + Senior**:
- [ ] Modificar `services/langchains_service/chain/rag_chain.py`
- [ ] Agregar retriever de Qdrant antes de llamar al LLM
- [ ] Construir prompt con contexto de documentos

**Archivo**: `services/langchains_service/chain/rag_chain.py`

#### 1.4 Alinear Variables de Entorno (1 hora)

**Tarea para Junior**:
- [ ] Documentar todas las variables en `.env.example`
- [ ] Crear script de validación de variables

**Entregables**:
- `environment_variables/.env.example`
- `scripts/validate_env.sh`

---

### 🟡 FASE 2: Refactor a Arquitectura Hexagonal (Días 4-7)

**Objetivo**: Separar capas, aplicar DDD

#### 2.1 Refactor LangChains Service (Días 4-5)

**Estructura propuesta**:
```
services/langchains_service/
├── domain/
│   ├── entities/
│   │   ├── query.py          # Entidad Query
│   │   └── conversation.py   # Entidad Conversation
│   ├── value_objects/
│   │   ├── embedding.py
│   │   └── document_chunk.py
│   ├── services/
│   │   └── rag_service.py    # Lógica de negocio RAG
│   └── repositories/
│       ├── document_repository.py  # Interface
│       └── conversation_repository.py
├── application/
│   ├── use_cases/
│   │   └── process_query_use_case.py
│   └── dto/
│       └── query_dto.py
├── infrastructure/
│   ├── adapters/
│   │   ├── qdrant_adapter.py
│   │   ├── embedding_client.py
│   │   └── ollama_client.py
│   └── config/
│       └── settings.py
└── presentation/
    ├── routes/
    │   └── query_routes.py
    └── schemas/
        └── query_schemas.py
```

**Tareas con Senior Architect**:

1. **Diseñar Entidades de Dominio** (2 horas)
   - [ ] Definir `Query` entity con validaciones
   - [ ] Definir `Conversation` entity
   - [ ] Crear value objects

2. **Implementar Servicio de Dominio** (3 horas)
   - [ ] `RAGService` con lógica pura de negocio
   - [ ] Sin dependencias de infraestructura
   - [ ] Testeable unitariamente

3. **Crear Interfaces de Repositorio** (1 hora)
   - [ ] `DocumentRepository` interface
   - [ ] `ConversationRepository` interface

4. **Implementar Caso de Uso** (2 horas)
   - [ ] `ProcessQueryUseCase` que orquesta:
     - Retrieval
     - Generación de respuesta
     - Persistencia de conversación

**Tareas para Junior (bajo supervisión)**:

- [ ] Crear estructura de carpetas
- [ ] Implementar adapters de infraestructura
- [ ] Migrar código existente a nuevas capas
- [ ] Crear tests unitarios básicos

**Archivos clave a crear**:
- `services/langchains_service/domain/entities/query.py`
- `services/langchains_service/domain/services/rag_service.py`
- `services/langchains_service/application/use_cases/process_query_use_case.py`
- `services/langchains_service/infrastructure/adapters/qdrant_adapter.py`

#### 2.2 Refactor Embedding Service (Día 6)

**Estructura**:
```
services/embedding_service/
├── domain/
│   ├── entities/
│   │   └── embedding.py
│   └── services/
│       └── embedding_service.py
├── application/
│   └── use_cases/
│       └── generate_embeddings_use_case.py
└── infrastructure/
    └── adapters/
        └── sentence_transformer_adapter.py
```

**Tareas**:
- [ ] Extraer lógica de embedding a dominio
- [ ] Agregar validación de inputs
- [ ] Implementar rate limiting básico

#### 2.3 Refactor API Gateway (Día 7)

**Tareas**:
- [ ] Implementar middleware de logging
- [ ] Agregar manejo de errores centralizado
- [ ] Crear schemas de validación

---

### 🟢 FASE 3: Mejoras de Infraestructura (Días 8-10)

#### 3.1 Configuración Centralizada (Día 8)

**Tarea para Junior**:
- [ ] Crear `core/config.py` con `pydantic-settings` en cada servicio
- [ ] Migrar todas las constantes hardcodeadas
- [ ] Documentar variables de entorno

#### 3.2 Healthchecks y Observabilidad (Día 9)

**Tareas**:
- [ ] Agregar `/health` y `/ready` en todos los servicios
- [ ] Configurar healthchecks en Docker Compose
- [ ] Implementar logging estructurado (JSON)

**Ejemplo para Junior**:
```python
# services/langchains_service/presentation/routes/health_routes.py
@app.get("/health")
async def health():
    return {"status": "healthy", "service": "langchains_service"}

@app.get("/ready")
async def ready():
    # Verificar dependencias
    try:
        # Test Qdrant connection
        # Test Embedding service
        return {"status": "ready"}
    except Exception as e:
        return {"status": "not_ready", "error": str(e)}, 503
```

#### 3.3 Manejo de Errores Robusto (Día 10)

**Tareas**:
- [ ] Agregar timeouts a todas las llamadas HTTP
- [ ] Implementar retry logic con backoff exponencial
- [ ] Crear excepciones de dominio personalizadas

**Ejemplo para Junior**:
```python
# services/langchains_service/infrastructure/adapters/http_client.py
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
async def call_service(url: str, payload: dict, timeout: float = 30.0):
    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.post(url, json=payload)
        response.raise_for_status()
        return response.json()
```

---

### 🔵 FASE 4: Testing y Documentación (Días 11-12)

#### 4.1 Testing (Día 11)

**Tareas con Senior**:
- [ ] Setup pytest en cada servicio
- [ ] Crear fixtures para servicios externos (mocks)
- [ ] Tests unitarios para servicios de dominio
- [ ] Tests de integración para casos de uso

**Ejemplo para Junior**:
```python
# tests/unit/domain/services/test_rag_service.py
def test_rag_service_retrieves_relevant_documents():
    # Arrange
    query = Query(text="test")
    mock_repo = MockDocumentRepository()
    
    # Act
    result = rag_service.process_query(query, mock_repo)
    
    # Assert
    assert len(result.documents) > 0
```

#### 4.2 Documentación (Día 12)

**Tareas**:
- [ ] Documentar APIs con OpenAPI/Swagger
- [ ] Crear diagramas de arquitectura
- [ ] Documentar flujos de trabajo
- [ ] Crear guía de contribución

---

## 🤝 Guía de Colaboración Junior + Senior

### Antes de Cada Fase

1. **Kickoff Meeting** (30 min)
   - Senior explica la arquitectura propuesta
   - Junior pregunta dudas
   - Se definen tareas específicas

2. **Pair Programming Sessions** (2-3 horas)
   - Senior codea junto con Junior
   - Se explican decisiones de diseño
   - Se revisa código en tiempo real

### Durante el Desarrollo

1. **Daily Standup** (15 min)
   - ¿Qué hice ayer?
   - ¿Qué haré hoy?
   - ¿Tengo bloqueos?

2. **Code Reviews**
   - Junior crea PR
   - Senior revisa y explica
   - Se iteran mejoras

### Al Final de Cada Fase

1. **Retrospectiva** (30 min)
   - ¿Qué salió bien?
   - ¿Qué mejorar?
   - Aprendizajes compartidos

---

## 📚 Glosario de Términos

**Bounded Context**: Límite dentro del cual un modelo de dominio es válido. Ej: "ETL" y "RAG" son contextos diferentes.

**Aggregate**: Cluster de entidades y value objects tratadas como unidad. Ej: `Document` es un agregado que contiene chunks y metadata.

**Entity**: Objeto con identidad única que persiste en el tiempo. Ej: `Query`, `Conversation`.

**Value Object**: Objeto inmutables definido por sus atributos. Ej: `EmbeddingVector`, `DocumentChunk`.

**Repository**: Abstracción para acceso a datos. La interfaz está en dominio, la implementación en infraestructura.

**Use Case**: Orquesta el flujo de aplicación. Ej: "ProcesarQuery" use case que coordina retrieval + generation.

**Adapter**: Implementación técnica que adapta servicios externos. Ej: `QdrantAdapter` adapta Qdrant a nuestro repositorio.

**Hexagonal Architecture**: Arquitectura que separa dominio (centro) de infraestructura (adaptadores externos).

**RAG (Retrieval Augmented Generation)**: Técnica que combina búsqueda de documentos relevantes + generación de texto.

**Embedding**: Representación numérica de texto en un espacio vectorial. Permite búsqueda semántica.

**ETL**: Extract (extraer), Transform (transformar), Load (cargar). Pipeline de procesamiento de datos.

---

## ✅ Checklist de Progreso

### Fase 0: Preparación
- [ ] Sesión de Domain Discovery completada
- [ ] Documentos de arquitectura creados
- [ ] Bounded contexts definidos

### Fase 1: Correcciones Críticas
- [ ] API Gateway corregido
- [ ] Docker Compose configurado correctamente
- [ ] RAG implementado con retrieval real
- [ ] Variables de entorno documentadas

### Fase 2: Refactor DDD
- [ ] LangChains Service refactorizado
- [ ] Embedding Service refactorizado
- [ ] API Gateway refactorizado
- [ ] Tests unitarios básicos implementados

### Fase 3: Infraestructura
- [ ] Configuración centralizada
- [ ] Healthchecks implementados
- [ ] Manejo de errores robusto

### Fase 4: Calidad
- [ ] Tests completos
- [ ] Documentación actualizada
- [ ] Code review completado

---

**¡Éxito en tu refactor! 🚀**

Si tienes dudas durante el proceso, consulta:
- Este documento
- El README.md principal
- Tu Senior Architect


