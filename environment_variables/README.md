# Variables de Entorno

Este directorio contiene los archivos de ejemplo para las variables de entorno necesarias en el proyecto.

## 📋 Archivos Disponibles

- `.env.rag.example` - Variables para el stack RAG (langchains_service)
- `.env.qdrant.example` - Variables para Qdrant (usado en ETL)

## 🚀 Configuración Inicial

1. **Copia los archivos de ejemplo:**
   ```bash
   cp .env.rag.example .env.rag
   cp .env.qdrant.example .env.qdrant
   ```

2. **Ajusta los valores según tu entorno:**
   - Edita `.env.rag` y `.env.qdrant` con tus valores específicos
   - Los valores por defecto funcionan para desarrollo local con Docker

## 📝 Variables en .env.rag

| Variable | Descripción | Valor por defecto |
|----------|-------------|-------------------|
| `QDRANT_URL` | URL del servicio Qdrant | `http://qdrant:6333` |
| `QDRANT_API_KEY` | API Key de Qdrant | `dev_key_123` |
| `QDRANT_COLLECTION_DOCS` | Colección de documentos | `embeddings_collection` |
| `QDRANT_COLLECTION_CONVERSATIONS` | Colección de conversaciones | `conversations` |
| `EMBEDDING_SERVICE_URL` | URL del servicio de embeddings | `http://embedding_service:8001/embedding` |
| `REDIS_HOST` | Host de Redis | `redis_service` |
| `REDIS_PORT` | Puerto de Redis | `6379` |
| `CACHE_TTL` | TTL del cache en segundos | `3600` |
| `OLLAMA_URL` | URL del servicio Ollama | `http://llm_service:11434` |
| `OLLAMA_MODEL` | Modelo de Ollama a usar | `llama3.2:3b` |

## 📝 Variables en .env.qdrant

| Variable | Descripción | Valor por defecto |
|----------|-------------|-------------------|
| `QDRANT_API_KEY` | API Key de Qdrant | `dev_key_123` |

## ⚠️ Importante

- Los archivos `.env.rag` y `.env.qdrant` están en `.gitignore` y **NO se commitean**
- Los archivos `.example` **SÍ se commitean** como plantillas
- Nunca subas archivos `.env` con valores sensibles al repositorio

## ✅ Validación

Puedes validar que las variables estén correctas usando:

```bash
./scripts/validate_env.sh environment_variables/.env.rag
./scripts/validate_env.sh environment_variables/.env.qdrant
```

