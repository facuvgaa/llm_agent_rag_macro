#!/bin/bash
# Script para mover /home a sda (119GB) - Opción A
# IMPORTANTE: Ejecutar con sudo bash configurar_discos.sh

set -e

echo "=========================================="
echo "Configuración: Mover /home a sda (119GB)"
echo "=========================================="
echo ""
echo "Estado actual de los discos:"
lsblk -o name,size,fstype,mountpoint | grep -E "NAME|^sd"
echo ""
echo "Estado del sistema:"
df -h / | tail -1
echo ""
echo "Tamaño de /home actual:"
du -sh /home 2>/dev/null || echo "Error al leer /home"
echo ""
echo "=========================================="
echo "Este script hará lo siguiente:"
echo "=========================================="
echo "1. Crear una partición en /dev/sda (119GB)"
echo "2. Formatear como ext4"
echo "3. Copiar todos los datos de /home a /dev/sda"
echo "4. Configurar /etc/fstab para montar /dev/sda en /home"
echo ""
echo "ADVERTENCIA: Esto eliminará todos los datos en /dev/sda"
echo "ADVERTENCIA: El sistema deberá reiniciarse después"
echo ""
echo "¿Deseas continuar? (escribe 'SI' para continuar)"
read -r confirmar

if [ "$confirmar" != "SI" ]; then
    echo "Operación cancelada."
    exit 0
fi

# Verificar que /dev/sda existe y no está montado
if [ ! -b /dev/sda ]; then
    echo "ERROR: /dev/sda no existe"
    exit 1
fi

if mountpoint -q /dev/sda 2>/dev/null || mount | grep -q /dev/sda; then
    echo "ERROR: /dev/sda está montado. Desmontar primero."
    exit 1
fi

echo ""
echo "=========================================="
echo "PASO 1: Creando tabla de particiones GPT en /dev/sda..."
echo "=========================================="
parted /dev/sda --script mklabel gpt

echo ""
echo "=========================================="
echo "PASO 2: Creando partición ext4 en /dev/sda..."
echo "=========================================="
parted /dev/sda --script mkpart primary ext4 0% 100%

# Esperar a que el kernel reconozca la nueva partición
sleep 2
partprobe /dev/sda
sleep 1

echo ""
echo "=========================================="
echo "PASO 3: Formateando /dev/sda1 como ext4..."
echo "=========================================="
mkfs.ext4 -F -L "home" /dev/sda1

echo ""
echo "=========================================="
echo "PASO 4: Obteniendo UUID de la nueva partición..."
echo "=========================================="
UUID=$(blkid -s UUID -o value /dev/sda1)
echo "UUID de /dev/sda1: $UUID"

echo ""
echo "=========================================="
echo "PASO 5: Creando punto de montaje temporal..."
echo "=========================================="
mkdir -p /mnt/home_new
mount /dev/sda1 /mnt/home_new

echo ""
echo "=========================================="
echo "PASO 6: Copiando datos de /home a /dev/sda1..."
echo "=========================================="
echo "Esto puede tardar varios minutos..."
rsync -aAXHv --info=progress2 --exclude={"/lost+found","/.cache","/.tmp"} /home/ /mnt/home_new/

echo ""
echo "=========================================="
echo "PASO 7: Verificando copia..."
echo "=========================================="
# Contar archivos en origen y destino
orig_count=$(find /home -type f 2>/dev/null | wc -l)
dest_count=$(find /mnt/home_new -type f 2>/dev/null | wc -l)
echo "Archivos en /home: $orig_count"
echo "Archivos copiados: $dest_count"

if [ "$dest_count" -lt "$orig_count" ]; then
    echo "ADVERTENCIA: Puede haber archivos no copiados. Revisar manualmente."
fi

echo ""
echo "=========================================="
echo "PASO 8: Haciendo backup de /etc/fstab..."
echo "=========================================="
cp /etc/fstab /etc/fstab.backup.$(date +%Y%m%d_%H%M%S)
echo "Backup guardado en /etc/fstab.backup.*"

echo ""
echo "=========================================="
echo "PASO 9: Actualizando /etc/fstab..."
echo "=========================================="
# Verificar si ya existe una entrada para /home
if grep -q "^[^#].*[[:space:]]/home[[:space:]]" /etc/fstab; then
    echo "ADVERTENCIA: Ya existe una entrada para /home en /etc/fstab"
    echo "Se comentará la línea antigua y se agregará la nueva"
    sed -i 's|^\([^#].*[[:space:]]/home[[:space:]].*\)|#\1|' /etc/fstab
fi

# Agregar nueva entrada
echo "" >> /etc/fstab
echo "# /home montado en /dev/sda1 (agregado automáticamente)" >> /etc/fstab
echo "UUID=$UUID /home ext4 defaults,noatime 0 2" >> /etc/fstab

echo "fstab actualizado correctamente"

echo ""
echo "=========================================="
echo "PROCESO COMPLETADO"
echo "=========================================="
echo ""
echo "RESUMEN:"
echo "- Partición creada: /dev/sda1"
echo "- UUID: $UUID"
echo "- Datos copiados a: /mnt/home_new"
echo "- /etc/fstab actualizado"
echo "- Backup de fstab: /etc/fstab.backup.*"
echo ""
echo "=========================================="
echo "PRÓXIMOS PASOS (IMPORTANTE):"
echo "=========================================="
echo ""
echo "1. Verificar que todo esté correcto:"
echo "   cat /etc/fstab | grep /home"
echo ""
echo "2. REINICIAR el sistema:"
echo "   sudo reboot"
echo ""
echo "3. Después del reinicio, verificar que /home esté montado en /dev/sda1:"
echo "   df -h /home"
echo "   mount | grep /home"
echo ""
echo "4. Si todo está bien, eliminar el directorio temporal (OPCIONAL):"
echo "   sudo umount /mnt/home_new"
echo "   sudo rm -rf /mnt/home_new"
echo ""
echo "5. Liberar espacio en el disco antiguo (OPCIONAL, después de verificar):"
echo "   sudo rm -rf /home/* (SOLO después de confirmar que todo funciona)"
echo ""
echo "=========================================="
echo "¡LISTO! El sistema está preparado."
echo "Reinicia cuando estés listo."
echo "=========================================="

