#!/bin/bash

# Script para instalar Docker y Docker Compose
# Compatible con Ubuntu/Debian y otras distribuciones Linux

set -e  # Salir si hay algún error

echo "🚀 Instalador de Docker y Docker Compose"
echo "=========================================="
echo ""

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Función para imprimir mensajes
info() {
    echo -e "${GREEN}✅ $1${NC}"
}

warn() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

error() {
    echo -e "${RED}❌ $1${NC}"
}

# Verificar si se ejecuta como root
if [ "$EUID" -eq 0 ]; then 
    error "No ejecutes este script como root. Se te pedirá sudo cuando sea necesario."
    exit 1
fi

# Detectar sistema operativo
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$ID
    VER=$VERSION_ID
else
    error "No se pudo detectar el sistema operativo"
    exit 1
fi

info "Sistema operativo detectado: $OS $VER"

# Verificar si Docker ya está instalado
if command -v docker &> /dev/null; then
    DOCKER_VERSION=$(docker --version)
    info "Docker ya está instalado: $DOCKER_VERSION"
else
    warn "Docker no está instalado. Instalando..."
    
    # Instalar dependencias
    info "Actualizando paquetes..."
    sudo apt-get update -qq
    
    info "Instalando dependencias..."
    sudo apt-get install -y -qq \
        ca-certificates \
        curl \
        gnupg \
        lsb-release
    
    # Agregar clave GPG de Docker
    info "Agregando clave GPG de Docker..."
    sudo mkdir -p /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/$OS/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    
    # Configurar repositorio
    info "Configurando repositorio de Docker..."
    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/$OS \
      $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    
    # Instalar Docker
    info "Instalando Docker..."
    sudo apt-get update -qq
    sudo apt-get install -y -qq docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
    
    info "Docker instalado correctamente"
fi

# Verificar si Docker Compose está disponible
if docker compose version &> /dev/null; then
    COMPOSE_VERSION=$(docker compose version)
    info "Docker Compose ya está disponible: $COMPOSE_VERSION"
elif command -v docker-compose &> /dev/null; then
    COMPOSE_VERSION=$(docker-compose --version)
    warn "Docker Compose v1 encontrado: $COMPOSE_VERSION"
    warn "Se recomienda usar Docker Compose v2 (plugin): docker compose"
else
    # Docker Compose v2 viene con Docker desde la versión 20.10+
    # Si no está, intentamos instalar el plugin
    warn "Docker Compose no encontrado. Verificando instalación..."
    
    # Verificar si el plugin está disponible
    if ! docker compose version &> /dev/null; then
        info "Instalando Docker Compose plugin..."
        sudo apt-get install -y -qq docker-compose-plugin
    fi
fi

# Verificar que Docker funcione
info "Verificando instalación de Docker..."
if sudo docker ps &> /dev/null; then
    info "Docker está funcionando correctamente"
else
    error "Docker no está funcionando. Intenta reiniciar el servicio:"
    echo "  sudo systemctl start docker"
    echo "  sudo systemctl enable docker"
    exit 1
fi

# Agregar usuario al grupo docker (para no usar sudo)
if ! groups $USER | grep -q docker; then
    warn "Agregando tu usuario al grupo 'docker' para no usar sudo..."
    sudo usermod -aG docker $USER
    info "Usuario agregado al grupo docker"
    warn "⚠️  IMPORTANTE: Debes cerrar sesión y volver a iniciar sesión para que los cambios surtan efecto"
    warn "O ejecuta: newgrp docker"
else
    info "Tu usuario ya está en el grupo docker"
fi

# Habilitar Docker al inicio
info "Habilitando Docker al inicio del sistema..."
sudo systemctl enable docker.service
sudo systemctl enable containerd.service

# Verificar instalación final
echo ""
echo "=========================================="
info "Verificación final:"
echo ""

# Verificar Docker
if docker --version &> /dev/null; then
    echo "  Docker: $(docker --version)"
else
    echo "  Docker: ❌ No disponible"
fi

# Verificar Docker Compose
if docker compose version &> /dev/null; then
    echo "  Docker Compose: $(docker compose version)"
elif command -v docker-compose &> /dev/null; then
    echo "  Docker Compose: $(docker-compose --version) (v1)"
else
    echo "  Docker Compose: ❌ No disponible"
fi

echo ""
info "✅ Instalación completada!"
echo ""
echo "📝 Próximos pasos:"
echo "  1. Si te agregó al grupo docker, cierra sesión y vuelve a iniciar"
echo "  2. O ejecuta: newgrp docker"
echo "  3. Verifica con: docker ps"
echo "  4. Usa 'make rag-up' o 'make etl-up' para levantar los servicios"
echo ""

