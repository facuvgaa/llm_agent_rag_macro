#!/bin/bash

# Script de validación de variables de entorno
# Uso: ./scripts/validate_env.sh [.env.rag|.env.qdrant]

set -e

ENV_FILE=${1:-"environment_variables/.env.rag"}

echo "🔍 Validando archivo: $ENV_FILE"
echo ""

if [ ! -f "$ENV_FILE" ]; then
    echo "❌ Error: Archivo $ENV_FILE no existe"
    exit 1
fi

# Cargar variables
set -a
source "$ENV_FILE"
set +a

# Variables requeridas según el archivo
if [[ "$ENV_FILE" == *".env.rag"* ]]; then
    echo "Validando variables para RAG stack..."
    
    REQUIRED_VARS=(
        "QDRANT_URL"
        "QDRANT_API_KEY"
        "EMBEDDING_SERVICE_URL"
        "OLLAMA_URL"
        "OLLAMA_MODEL"
    )
    
    for var in "${REQUIRED_VARS[@]}"; do
        if [ -z "${!var}" ]; then
            echo "❌ Variable requerida faltante: $var"
            exit 1
        else
            echo "✅ $var=${!var}"
        fi
    done
    
elif [[ "$ENV_FILE" == *".env.qdrant"* ]]; then
    echo "Validando variables para Qdrant..."
    
    if [ -z "$QDRANT_API_KEY" ]; then
        echo "❌ QDRANT_API_KEY no definida"
        exit 1
    else
        echo "✅ QDRANT_API_KEY está definida"
    fi
fi

echo ""
echo "✅ Todas las variables requeridas están presentes"


