#!/bin/bash
# Script para diagnosticar la conexión entre frontend y API Gateway

echo "=========================================="
echo "🔍 DIAGNÓSTICO DE CONEXIÓN FRONTEND-API"
echo "=========================================="

echo ""
echo "1. Verificando que el API Gateway esté corriendo..."
if docker ps --filter "name=gateway_service" --format "{{.Names}}" | grep -q gateway_service; then
    echo "✅ API Gateway está corriendo"
else
    echo "❌ API Gateway NO está corriendo"
    echo "   Ejecuta: docker compose -f infra/docker-compose.rag.yml up -d gateway_service"
    exit 1
fi

echo ""
echo "2. Probando conexión directa al API Gateway..."
RESPONSE=$(curl -s -X POST http://localhost:8000/rag/ \
    -H "Content-Type: application/json" \
    -d '{"pregunta": "test"}' \
    --max-time 10)

if [ $? -eq 0 ] && echo "$RESPONSE" | grep -q "respuesta"; then
    echo "✅ API Gateway responde correctamente"
    echo "   Respuesta: $(echo "$RESPONSE" | head -c 100)..."
else
    echo "❌ API Gateway NO responde correctamente"
    echo "   Respuesta: $RESPONSE"
    exit 1
fi

echo ""
echo "3. Verificando CORS en el API Gateway..."
CORS_CHECK=$(curl -s -X OPTIONS http://localhost:8000/rag/ \
    -H "Origin: http://localhost:3000" \
    -H "Access-Control-Request-Method: POST" \
    -v 2>&1 | grep -i "access-control-allow-origin" || echo "")

if echo "$CORS_CHECK" | grep -q "localhost:3000"; then
    echo "✅ CORS está configurado correctamente"
else
    echo "⚠️  CORS puede no estar configurado correctamente"
    echo "   Verifica que app.py tenga CORSMiddleware configurado"
fi

echo ""
echo "4. Verificando que el frontend pueda conectarse (simulando petición del navegador)..."
BROWSER_TEST=$(curl -s -X POST http://localhost:8000/rag/ \
    -H "Content-Type: application/json" \
    -H "Origin: http://localhost:3000" \
    -d '{"pregunta": "test desde navegador"}' \
    --max-time 10)

if [ $? -eq 0 ] && echo "$BROWSER_TEST" | grep -q "respuesta"; then
    echo "✅ El API Gateway acepta peticiones del frontend"
else
    echo "❌ Problema con peticiones desde el frontend"
    echo "   Respuesta: $BROWSER_TEST"
fi

echo ""
echo "5. Verificando logs recientes del API Gateway..."
echo "   Últimas líneas de log:"
docker logs gateway_service --tail 5 2>&1 | tail -3

echo ""
echo "=========================================="
echo "📝 INSTRUCCIONES:"
echo "=========================================="
echo ""
echo "Si todo está ✅, entonces:"
echo "1. Asegúrate de que el frontend esté corriendo:"
echo "   cd frontend && npm run dev"
echo ""
echo "2. Abre el navegador en: http://localhost:3000"
echo ""
echo "3. Abre la consola del navegador (F12) y busca errores"
echo ""
echo "4. Intenta enviar un mensaje y revisa:"
echo "   - La consola del navegador (F12)"
echo "   - Los logs del API Gateway: docker logs gateway_service --tail 20"
echo ""
echo "=========================================="

