#!/bin/bash

# Script para iniciar el Dashboard completo en macOS/Linux

echo ""
echo "======================================================================"
echo "    🚀 INICIANDO DASHBOARD COMPLETO - Be Digital"
echo "======================================================================"
echo ""

# Verificar si Node.js está instalado
if ! command -v node &> /dev/null; then
    echo "❌ Node.js no está instalado"
    echo "   Descarga desde: https://nodejs.org/"
    exit 1
fi

# Verificar si Python está instalado
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 no está instalado"
    exit 1
fi

echo "✅ Node.js detectado"
echo "✅ Python detectado"
echo ""

# Verificar si package.json existe
if [ ! -f "package.json" ]; then
    echo "❌ package.json no encontrado"
    echo "   Asegúrate de estar en la carpeta correcta"
    exit 1
fi

echo "📦 Instalando dependencias de React..."
npm install
if [ $? -ne 0 ]; then
    echo "❌ Error en npm install"
    exit 1
fi

echo "✅ Dependencias instaladas"
echo ""

echo "🔨 Compilando React (npm run build)..."
npm run build
if [ $? -ne 0 ]; then
    echo "❌ Error en build"
    exit 1
fi

echo "✅ React compilado"
echo ""

# Instalar Flask-CORS si no está
pip3 install flask-cors > /dev/null 2>&1

echo "======================================================================"
echo "    ✅ SETUP COMPLETADO - Iniciando servicios..."
echo "======================================================================"
echo ""

echo "Se abrirán 3 terminales:"
echo "  1. Terminal 1: Script principal (main.py)"
echo "  2. Terminal 2: Backend Flask (api.py)"
echo "  3. Terminal 3: Frontend React (npm start)"
echo ""
echo "El navegador se abrirá automáticamente en: http://localhost:3000"
echo ""

# Crear función para abrir terminal
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    echo "🍎 Detectado macOS"
    echo ""
    
    open -a Terminal "$(dirname "$0")" &
    sleep 1
    
    # Terminal 1
    osascript <<EOF
        tell application "Terminal"
            do script "cd '$(pwd)' && python main.py" in window 1
        end tell
EOF
    
    sleep 1
    
    # Terminal 2
    osascript <<EOF
        tell application "Terminal"
            do script "cd '$(pwd)' && python api.py" in new window
        end tell
EOF
    
    sleep 1
    
    # Terminal 3
    osascript <<EOF
        tell application "Terminal"
            do script "cd '$(pwd)' && npm start" in new window
        end tell
EOF
    
    sleep 3
    open http://localhost:3000
else
    # Linux
    echo "🐧 Detectado Linux"
    echo ""
    
    # Intentar abrir con gnome-terminal
    if command -v gnome-terminal &> /dev/null; then
        gnome-terminal --tab --title="main.py" -- bash -c "cd '$(pwd)'; python main.py; bash"
        sleep 1
        gnome-terminal --tab --title="api.py" -- bash -c "cd '$(pwd)'; python api.py; bash"
        sleep 1
        gnome-terminal --tab --title="React" -- bash -c "cd '$(pwd)'; npm start; bash"
    elif command -v xterm &> /dev/null; then
        xterm -e "cd '$(pwd)'; python main.py" &
        sleep 1
        xterm -e "cd '$(pwd)'; python api.py" &
        sleep 1
        xterm -e "cd '$(pwd)'; npm start" &
    else
        echo "⚠️  No se encontró terminal gráfica"
        echo "   Abre 3 terminales manualmente y ejecuta:"
        echo ""
        echo "   Terminal 1: python main.py"
        echo "   Terminal 2: python api.py"
        echo "   Terminal 3: npm start"
        exit 0
    fi
    
    sleep 3
    if command -v xdg-open &> /dev/null; then
        xdg-open http://localhost:3000
    fi
fi

echo ""
echo "======================================================================"
echo "    🎉 TODO INICIADO - Abre: http://localhost:3000"
echo "======================================================================"
echo ""
