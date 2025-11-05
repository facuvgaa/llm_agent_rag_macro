# Agent Full - Sistema RAG Banco Macro

Sistema de Retrieval Augmented Generation (RAG) para el Banco Macro que permite hacer consultas sobre documentos usando Inteligencia Artificial.

## 🎥 Demo del Sistema

![Demo del Sistema RAG](docs/gifs/Grabación-de-pantalla-desde-2025-11-05-03-39-45.gif)

*Demo visual del sistema RAG en funcionamiento*

## 📋 Arquitectura del Sistema

![Diagrama de Arquitectura](docs/images/arquitectura-rag.excalidraw)

El sistema está compuesto por dos partes principales:

### 1. ETL (Extract, Transform, Load)
- **Leer URLs**: Lee URLs de documentos desde `services/airflow_dags/urls.txt`
- **Chunkear PDFs**: Divide los PDFs en chunks más pequeños usando [pdf-chunk-flow](https://pypi.org/project/pdf-chunk-flow/)
- **Generar Embeddings**: Convierte los chunks en vectores de 768 dimensiones usando [embedding-flow](https://pypi.org/project/embedding-flow/)
- **Publicar a Kafka**: Notifica cuando el proceso ETL está completo
- **Almacenar en Qdrant**: Guarda los embeddings en la base de datos vectorial (usando embedding-flow)

### 2. RAG System
- **API Gateway**: Punto de entrada para las consultas de los usuarios
- **LangChains Service**: Orquestador central que coordina todo el flujo
- **Embedding Service**: Genera embeddings de las consultas de los usuarios
- **Qdrant Service**: Base de datos vectorial para búsqueda semántica
- **Redis**: Cache y memoria de conversaciones
- **LLM Service (Ollama)**: Modelo de lenguaje para generar respuestas

## 🚀 Inicio Rápido

### Instalación de Prerequisitos

Si no tienes Docker y Docker Compose instalados, ejecuta:

```bash
# Instalar Docker y Docker Compose automáticamente
./scripts/install_docker.sh
```

Este script:
- ✅ Detecta tu sistema operativo
- ✅ Instala Docker si no está instalado
- ✅ Instala Docker Compose v2 (plugin)
- ✅ Configura tu usuario para usar Docker sin sudo
- ✅ Habilita Docker al inicio del sistema

**Nota:** Después de ejecutar el script, si te agregó al grupo docker, cierra sesión y vuelve a iniciar, o ejecuta `newgrp docker`.

### Configuración de Variables de Entorno

```bash
# Copiar archivos de ejemplo
cp environment_variables/.env.rag.example environment_variables/.env.rag
cp environment_variables/.env.qdrant.example environment_variables/.env.qdrant

# Ajustar valores si es necesario (los defaults funcionan para desarrollo)
```

### Levantar servicios

```bash
# Levantar stack ETL
make etl-up

# Levantar stack RAG
make rag-up
```

### Detener servicios

```bash
# Detener stack ETL
make etl-down

# Detener stack RAG
make rag-down
```

## 🌐 Acceso a los Servicios

Una vez levantados los servicios, puedes acceder a:

| Servicio | URL | Descripción |
|----------|-----|-------------|
| **Frontend** | http://localhost:3000 | Interfaz web del chatbot RAG |
| **API Gateway** | http://localhost:8000 | API REST para consultas RAG |
| **Airflow (ETL)** | http://localhost:8080 | Interfaz web de Airflow para gestionar DAGs |
| **Qdrant** | http://localhost:6333 | Interfaz web de Qdrant (base de datos vectorial) |
| **LangChains Service** | http://localhost:8002 | Servicio RAG directamente |
| **Embedding Service** | http://localhost:8001 | Servicio de embeddings |
| **Ollama** | http://localhost:11434 | API de Ollama |

**Nota:** Los servicios internos (Redis, etc.) no están expuestos externamente por seguridad.

## 📁 Estructura del Proyecto

```
agent-full/
├── infra/
│   ├── docker-compose.etl.yml    # Servicios ETL
│   └── docker-compose.rag.yml     # Servicios RAG
├── services/
│   ├── api_gateway/              # API Gateway
│   ├── langchains_service/       # Servicio RAG principal
│   ├── embedding_service/        # Generación de embeddings
│   ├── airflow_dags/             # DAGs de Airflow para ETL
│   └── ...
├── docker/                        # Dockerfiles de servicios
├── docs/                          # Documentación
│   └── images/                    # Diagramas y diagramas
└── environment_variables/         # Variables de entorno
```

## 🔧 Configuración

### Variables de Entorno

Ver `environment_variables/.env.rag` y `environment_variables/.env.qdrant` para configurar las variables de entorno necesarias.

### Personalización de PDFs

Para agregar o modificar los PDFs que se procesan en el ETL, edita el archivo:

```
services/airflow_dags/urls.txt
```

Cada línea del archivo debe contener una URL válida de un PDF. El DAG de Airflow procesará todos los PDFs listados en este archivo.

## 🛠️ Tecnologías y Librerías

### Stack Tecnológico Principal

- **Backend**:
  - **Python 3.12+**: Lenguaje principal para servicios backend
  - **FastAPI**: Framework web para API Gateway y servicios
  - **Uvicorn**: Servidor ASGI para FastAPI
  - **LangChain/LangGraph**: Framework para orquestación RAG y flujos de trabajo
  - **LangChain Ollama**: Integración con Ollama para modelos locales

- **Frontend**:
  - **Next.js**: Framework React para la interfaz de usuario
  - **React**: Biblioteca para interfaces de usuario
  - **TypeScript**: Tipado estático para JavaScript
  - **Tailwind CSS**: Framework CSS para estilos

- **Bases de Datos y Almacenamiento**:
  - **Qdrant**: Base de datos vectorial para búsqueda semántica
  - **Redis**: Cache y memoria de conversaciones
  - **Supabase**: Backend como servicio (PostgreSQL) para el frontend

- **Infraestructura y Orquestación**:
  - **Docker & Docker Compose**: Contenedorización y orquestación
  - **Airflow**: Orquestación de workflows ETL
  - **Kafka**: Mensajería y eventos asíncronos

- **Modelos de IA**:
  - **Ollama**: Servidor para ejecutar modelos LLM localmente
  - **llama3.2:3b**: Modelo de lenguaje utilizado

### Procesamiento de PDFs y Embeddings

El sistema utiliza librerías propias desarrolladas específicamente para este proyecto:

- **[pdf-chunk-flow](https://pypi.org/project/pdf-chunk-flow/)**: Librería para chunkear PDFs
  - Utilizada para dividir documentos PDF en chunks más pequeños
  - Configuración: **768 dimensiones** con **overlap activado** para mejorar la coherencia contextual

- **[embedding-flow](https://pypi.org/project/embedding-flow/)**: Librería para generar embeddings y cargar en Qdrant
  - Genera embeddings vectoriales de los chunks
  - Carga automática de embeddings en Qdrant
  - Configuración: **768 dimensiones** (compatible con el modelo de embeddings usado)

### Modelo de Lenguaje

- **LLM**: `llama3.2:3b` ejecutándose en Ollama
  - Modelo de lenguaje pequeño y eficiente para generación de respuestas
  - Configurado en `services/langchains_service/chain/rag_chain.py`

## 📚 Documentación

- Diagrama de arquitectura: `docs/images/arquitectura-rag.excalidraw`

## 🙏 Agradecimientos

Este proyecto utiliza el frontend de [Chatbot UI](https://github.com/mckaywrigley/chatbot-ui) desarrollado por [mckaywrigley](https://github.com/mckaywrigley). Agradecemos su excelente trabajo y contribución a la comunidad open source.

## 👤 Autor

**Facundo Vega**

Desarrollador del sistema RAG y las librerías utilizadas en este proyecto.

### 🔗 Redes y Contacto

- **LinkedIn**: [wfvega](https://www.linkedin.com/in/wfvega/)

### 📦 Librerías Propias

Este proyecto utiliza librerías desarrolladas por el autor:

- **PyPI**: [facuvega](https://pypi.org/user/facuvega/)
  - Todas las librerías disponibles en PyPI
- **GitHub**: [facuvegaingenieer](https://github.com/facuvegaingenieer)
  - Repositorios de las librerías:
    - [pdf-chunk-flow](https://github.com/facuvegaingenieer/pdf_chunk_flow)
    - [embedding-flow](https://github.com/facuvegaingenieer/macro-embedding-flow)
    - Y más...

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo [LICENSE](LICENSE) para más detalles.

---

# Agent Full - Macro Bank RAG System

RAG (Retrieval Augmented Generation) system for Macro Bank that allows querying documents using Artificial Intelligence.

## 🎥 System Demo

![RAG System Demo](docs/gifs/Grabación-de-pantalla-desde-2025-11-05-03-39-45.gif)

*Visual demo of the RAG system in operation*

## 📋 System Architecture

![Architecture Diagram](docs/images/arquitectura-rag.excalidraw)

The system consists of two main parts:

### 1. ETL (Extract, Transform, Load)
- **Read URLs**: Reads document URLs from `services/airflow_dags/urls.txt`
- **Chunk PDFs**: Divides PDFs into smaller chunks using [pdf-chunk-flow](https://pypi.org/project/pdf-chunk-flow/)
- **Generate Embeddings**: Converts chunks into 768-dimensional vectors using [embedding-flow](https://pypi.org/project/embedding-flow/)
- **Publish to Kafka**: Notifies when the ETL process is complete
- **Store in Qdrant**: Saves embeddings in the vector database (using embedding-flow)

### 2. RAG System
- **API Gateway**: Entry point for user queries
- **LangChains Service**: Central orchestrator that coordinates the entire flow
- **Embedding Service**: Generates embeddings for user queries
- **Qdrant Service**: Vector database for semantic search
- **Redis**: Cache and conversation memory
- **LLM Service (Ollama)**: Language model for generating responses

## 🚀 Quick Start

### Prerequisites Installation

If you don't have Docker and Docker Compose installed, run:

```bash
# Automatically install Docker and Docker Compose
./scripts/install_docker.sh
```

This script:
- ✅ Detects your operating system
- ✅ Installs Docker if not installed
- ✅ Installs Docker Compose v2 (plugin)
- ✅ Configures your user to use Docker without sudo
- ✅ Enables Docker on system startup

**Note:** After running the script, if it added you to the docker group, log out and log back in, or run `newgrp docker`.

### Environment Variables Configuration

```bash
# Copy example files
cp environment_variables/.env.rag.example environment_variables/.env.rag
cp environment_variables/.env.qdrant.example environment_variables/.env.qdrant

# Adjust values if necessary (defaults work for development)
```

### Start Services

```bash
# Start ETL stack
make etl-up

# Start RAG stack
make rag-up
```

### Stop Services

```bash
# Stop ETL stack
make etl-down

# Stop RAG stack
make rag-down
```

## 🌐 Service Access

Once services are up, you can access:

| Service | URL | Description |
|---------|-----|-------------|
| **Frontend** | http://localhost:3000 | RAG chatbot web interface |
| **API Gateway** | http://localhost:8000 | REST API for RAG queries |
| **Airflow (ETL)** | http://localhost:8080 | Airflow web interface for managing DAGs |
| **Qdrant** | http://localhost:6333 | Qdrant web interface (vector database) |
| **LangChains Service** | http://localhost:8002 | RAG service directly |
| **Embedding Service** | http://localhost:8001 | Embedding service |
| **Ollama** | http://localhost:11434 | Ollama API |

**Note:** Internal services (Redis, etc.) are not exposed externally for security.

## 📁 Project Structure

```
agent-full/
├── infra/
│   ├── docker-compose.etl.yml    # ETL services
│   └── docker-compose.rag.yml     # RAG services
├── services/
│   ├── api_gateway/              # API Gateway
│   ├── langchains_service/       # Main RAG service
│   ├── embedding_service/        # Embedding generation
│   ├── airflow_dags/             # Airflow DAGs for ETL
│   └── ...
├── docker/                        # Service Dockerfiles
├── docs/                          # Documentation
│   └── images/                    # Diagrams and images
└── environment_variables/         # Environment variables
```

## 🔧 Configuration

### Environment Variables

See `environment_variables/.env.rag` and `environment_variables/.env.qdrant` to configure the necessary environment variables.

### PDF Customization

To add or modify PDFs processed in the ETL, edit the file:

```
services/airflow_dags/urls.txt
```

Each line of the file must contain a valid PDF URL. The Airflow DAG will process all PDFs listed in this file.

## 🛠️ Technologies and Libraries

### Main Technology Stack

- **Backend**:
  - **Python 3.12+**: Main language for backend services
  - **FastAPI**: Web framework for API Gateway and services
  - **Uvicorn**: ASGI server for FastAPI
  - **LangChain/LangGraph**: Framework for RAG orchestration and workflows
  - **LangChain Ollama**: Integration with Ollama for local models

- **Frontend**:
  - **Next.js**: React framework for user interface
  - **React**: Library for user interfaces
  - **TypeScript**: Static typing for JavaScript
  - **Tailwind CSS**: CSS framework for styling

- **Databases and Storage**:
  - **Qdrant**: Vector database for semantic search
  - **Redis**: Cache and conversation memory
  - **Supabase**: Backend as a service (PostgreSQL) for frontend

- **Infrastructure and Orchestration**:
  - **Docker & Docker Compose**: Containerization and orchestration
  - **Airflow**: ETL workflow orchestration
  - **Kafka**: Messaging and asynchronous events

- **AI Models**:
  - **Ollama**: Server for running LLM models locally
  - **llama3.2:3b**: Language model used

### PDF Processing and Embeddings

The system uses custom libraries developed specifically for this project:

- **[pdf-chunk-flow](https://pypi.org/project/pdf-chunk-flow/)**: Library for chunking PDFs
  - Used to divide PDF documents into smaller chunks
  - Configuration: **768 dimensions** with **overlap enabled** to improve contextual coherence

- **[embedding-flow](https://pypi.org/project/embedding-flow/)**: Library for generating embeddings and loading into Qdrant
  - Generates vector embeddings of chunks
  - Automatic loading of embeddings into Qdrant
  - Configuration: **768 dimensions** (compatible with the embedding model used)

### Language Model

- **LLM**: `llama3.2:3b` running on Ollama
  - Small and efficient language model for response generation
  - Configured in `services/langchains_service/chain/rag_chain.py`

## 📚 Documentation

- Architecture diagram: `docs/images/arquitectura-rag.excalidraw`

## 🙏 Acknowledgments

This project uses the frontend from [Chatbot UI](https://github.com/mckaywrigley/chatbot-ui) developed by [mckaywrigley](https://github.com/mckaywrigley). We thank them for their excellent work and contribution to the open source community.

## 👤 Author

**Facundo Vega**

Developer of the RAG system and libraries used in this project.

### 🔗 Networks and Contact

- **LinkedIn**: [wfvega](https://www.linkedin.com/in/wfvega/)

### 📦 Custom Libraries

This project uses libraries developed by the author:

- **PyPI**: [facuvega](https://pypi.org/user/facuvega/)
  - All libraries available on PyPI
- **GitHub**: [facuvegaingenieer](https://github.com/facuvegaingenieer)
  - Library repositories:
    - [pdf-chunk-flow](https://github.com/facuvegaingenieer/pdf_chunk_flow)
    - [embedding-flow](https://github.com/facuvegaingenieer/macro-embedding-flow)
    - And more...

## 📄 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for more details.
