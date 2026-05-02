# Monitor de Dispositivos Android - Be Digital

## Descripcion del Proyecto

Sistema de automatizacion paralela para dispositivos Android que permite monitorear y controlar multiples dispositivos simultaneamente. Incluye un dashboard en tiempo real que detecta conexiones/desconexiones de dispositivos, bateria, almacenamiento y ejecucion de acciones personalizadas.

---

## Caracteristicas Principales

- Deteccion automatica de dispositivos (detecta dispositivos fisicos y emuladores via ADB)
- Ejecucion paralela (ejecuta tareas en multiples dispositivos simultaneamente)
- Monitoreo en tiempo real (dashboard que se actualiza automaticamente cada 5 segundos)
- Deteccion de desconexiones (identifica automaticamente cuando un dispositivo se desconecta)
- Recoleccion de datos:
  - Nivel de bateria
  - Informacion de almacenamiento
  - Captura de pantalla automatica
  - Aperturas de aplicaciones
- Almacenamiento persistente (guarda datos en archivos locales y API externa)
- Interfaz profesional (dashboard React responsivo con graficos y estadisticas)

---

## Requisitos Previos

### Software Obligatorio

- Python 3.8 o superior - https://www.python.org/downloads/
- Node.js 14 o superior - https://nodejs.org/
- Android SDK (incluye ADB - Android Debug Bridge)
- Git (opcional)

### Requisitos del Sistema

- Windows 10+, macOS 10.12+ o Linux Ubuntu 18.04+
- Minimo 2GB RAM disponible
- Minimo 500MB espacio en disco
- Conexion a internet (para API externa)

### Dispositivos Android

- Android 5.0 o superior (para depuracion USB)
- Depuracion USB habilitada
- Conexion USB o emulador de Android Studio

---

## Instalacion Paso a Paso

### PASO 1: Descargar e Instalar Requisitos

#### 1.1 Python
```bash
# Verificar que Python esta instalado
python --version
# Debe mostrar: Python 3.8.0 o superior
```

#### 1.2 Node.js
```bash
# Verificar que Node.js esta instalado
node --version
npm --version
# Deben mostrar versiones v14.0.0+ y 6.0.0+
```

#### 1.3 Android SDK (ADB)

Windows:
1. Descargar Android Studio: https://developer.android.com/studio
2. Durante la instalacion, seleccionar "Android SDK"
3. Abrir SDK Manager (Tools >> SDK Manager)
4. Verificar que esta instalado "Android SDK Platform-Tools"
5. Agregar ADB al PATH del sistema:
   - Sistema >> Variables de entorno >> Path
   - Agregar: C:\Users\[TuUsuario]\AppData\Local\Android\Sdk\platform-tools

macOS:
```bash
# Con Homebrew
brew install android-platform-tools

# Verificar
adb version
```

Linux (Ubuntu/Debian):
```bash
sudo apt update
sudo apt install android-tools-adb android-tools-fastboot

# Verificar
adb version
```

---

### PASO 2: Preparar la Carpeta del Proyecto

```bash
# Crear carpeta del proyecto
mkdir Be_Digital
cd Be_Digital

# Crear estructura de carpetas
mkdir venv logs outputs src public src/components
```

---

### PASO 3: Crear Entorno Virtual de Python

```bash
# Crear entorno virtual
python -m venv venv

# Activar entorno virtual

# Windows:
venv\Scripts\activate

# macOS/Linux:
source venv/bin/activate
```

Despues de activar, el prompt debe mostrar: (venv) C:\ruta\Be_Digital>

---

### PASO 4: Instalar Dependencias de Python

```bash
# Asegurate que venv esta activado (debe ver "(venv)" en el prompt)

# Instalar dependencias
pip install requests==2.31.0 python-dotenv==1.0.0 Pillow==10.0.0 flask==2.3.0 flask-cors==4.0.0

# O instalar desde requirements.txt si lo tienes:
pip install -r requirements.txt
```

Paquetes instalados:
- requests==2.31.0: Para hacer peticiones HTTP
- python-dotenv==1.0.0: Para variables de entorno
- Pillow==10.0.0: Para procesar imagenes (screenshots)
- Flask==2.3.0: Backend web
- Flask-CORS==4.0.0: Soporte CORS para el dashboard

---

### PASO 5: Instalar Dependencias de Node.js

```bash
# Debe estar en la carpeta Be_Digital
npm install
```

Paquetes instalados:
- react: Framework de frontend
- react-dom: Renderizado DOM
- axios: Cliente HTTP
- recharts: Graficos

---

### PASO 6: Descargar Archivos del Proyecto

 Clonar el repositorio del proyecto

git clone https://github.com/zFerchou/automatizacion_Be_Digital.git

 Entrar a la carpeta del proyecto
cd Be_Digital



### PASO 7: Configurar Variables de Entorno

Crea/edita el archivo .env en la raiz del proyecto:

```env
# API Endpoint (opcional - para enviar datos a servidor externo)
API_ENDPOINT=https://tu-api.com/endpoint

# Carpeta de salida para datos
OUTPUT_FOLDER=./outputs

# Carpeta para logs
LOG_FOLDER=./logs

# App a ejecutar en Android
SETTINGS_APP=com.android.settings
```

---

### PASO 8: Compilar React

```bash
# Compilar el frontend
npm run build

# Esto crea una carpeta 'build/' con el dashboard listo para produccion
```

---

### PASO 9: Conectar Dispositivos Android

Dispositivo Fisico:
1. Conecta el dispositivo via USB
2. En el dispositivo: Configuracion >> Desarrollador >> Depuracion USB (habilitar)
3. En terminal, ejecuta:
```bash
adb devices
# Debe listar tu dispositivo
```

Emulador:
1. Abre Android Studio
2. Crea o inicia un emulador
3. El emulador aparecera automaticamente en adb devices

---

## Ejecutar el Proyecto

### Opcion A: Script Automatico 

Windows:
```bash
# Doble-click en:
INICIAR_DASHBOARD.bat
```

macOS/Linux:
```bash
chmod +x INICIAR_DASHBOARD.sh
./INICIAR_DASHBOARD.sh
```

### Opcion B: Manual (3 Terminales)

Terminal 1: Ejecutar main.py
```bash
# Asegurate que venv esta activo
(venv) C:\Be_Digital> python main.py
```

Terminal 2: Ejecutar API Flask
```bash
# Asegurate que venv esta activo
(venv) C:\Be_Digital> python api.py
```

Terminal 3: Ejecutar Frontend React
```bash
npm start
```

---

## Acceder al Dashboard

Una vez que todo esta corriendo:

Abre en navegador: http://localhost:3000

El dashboard muestra:
- Dispositivos conectados en tiempo real
- Nivel de bateria de cada dispositivo
- Almacenamiento disponible
- Screenshots capturados (con enlace para ver)
- Historico de ejecuciones
- Dispositivos desconectados
- Boton para ejecutar main.py desde el dashboard


## Flujo de Datos

```
FLUJO DE EJECUCION:

1. Terminal 1: python main.py
   - Detecta dispositivos via ADB
   - Ejecuta tareas en paralelo (threading)
   - Recolecta: bateria, almacenamiento, screenshots
   - Guarda datos en ./outputs/device_*.txt
   - Envia a API externa (si configurada)

2. Terminal 2: python api.py
   - Inicia servidor Flask en puerto 5000
   - Lee archivos de ./outputs/
   - Detecta desconexiones automaticamente
   - Sirve datos via API REST

3. Terminal 3: npm start
   - Inicia servidor React en puerto 3000
   - Realiza peticiones cada 5 segundos a /api/devices
   - Actualiza dashboard en tiempo real
   - Permite ejecutar main.py desde boton

4. Navegador: http://localhost:3000
   - Muestra dashboard actualizado
   - Permite interaccion con el sistema
```

---

## Endpoints de la API

BASE URL: http://localhost:5000

GET /api/devices
- Retorna dispositivos conectados y desconectados
- Response: {
    "connected": [dispositivos activos],
    "disconnected": [dispositivos inactivos],
    "all": [todos los dispositivos]
  }

GET /api/status
- Retorna estado general del sistema
- Response: {
    "dispositivos_conectados": numero,
    "total_ejecuciones": numero,
    "estado": "activo"
  }

GET /api/history
- Retorna ultimas 100 ejecuciones
- Response: [array de ejecuciones]

POST /api/run-main
- Ejecuta main.py desde el frontend
- Response: dispositivos actualizados

GET /api/screenshot/<filename>
- Sirve imagen de screenshot
- Response: archivo JPEG

GET /api/health
- Health check del servidor
- Response: {status: "ok"}

---

## Datos Recolectados

Cada ejecucion recolecta:

```json
{
  "id_dispositivo": "RFCW41H4ESH",
  "timestamp_iso": "2026-05-02T10:30:45.123456",
  "timestamp_legible": "02/05/2026 10:30:45",
  "bateria": {
    "porcentaje": 85,
    "unidad": "%"
  },
  "almacenamiento": {
    "total_mb": 108349,
    "usado_mb": 46472,
    "disponible_mb": 61877,
    "porcentaje_libre": 57.05,
    "unidad": "MB"
  },
  "acciones": {
    "app_abierta": "com.android.settings",
    "screenshot_tomado": true,
    "almacenamiento_bajo": false
  },
  "screenshots": [
    "screenshot_RFCW41H4ESH_20260502_103045.jpg"
  ]
}
```

---

## Troubleshooting

### Error: "adb: command not found"

Solucion:
- Windows: Agregar ADB al PATH del sistema
  1. Abre "Variables de entorno" en Windows
  2. Edita la variable "Path"
  3. Agrega: C:\Users\[TuUsuario]\AppData\Local\Android\Sdk\platform-tools

- macOS/Linux:
```bash
export PATH=$PATH:~/Library/Android/sdk/platform-tools  # macOS
export PATH=$PATH:~/Android/Sdk/platform-tools           # Linux
```

### Error: "port 3000 is already in use"

Solucion:
```bash
# Usar otro puerto
PORT=3001 npm start

# O matar el proceso
# Windows:
netstat -ano | findstr :3000
taskkill /PID <PID> /F

# macOS/Linux:
lsof -ti:3000 | xargs kill -9
```

### Error: "Python module not found"

Solucion:
```bash
# Asegurate que venv esta activo
# Windows:
venv\Scripts\activate

# macOS/Linux:
source venv/bin/activate

# Reinstala dependencias
pip install -r requirements.txt
```

### Dispositivo no detectado

Solucion:
```bash
# Verificar conectividad
adb devices

# Si aparece como "offline":
adb kill-server
adb start-server
adb devices

# Verificar depuracion USB en el dispositivo:
# Configuracion >> Desarrollador >> Depuracion USB (ON)
```

### Dashboard no muestra datos

Solucion:
1. Verifica que las 3 terminales estan corriendo
2. Presiona el boton "Ejecutar main.py"
3. Espera 5-10 segundos
4. Recarga navegador (F5)
5. Revisa la consola del navegador (F12 >> Console)

---

## Comandos ADB Utiles

```bash
# Listar dispositivos conectados
adb devices

# Conectar por IP (si no esta por USB)
adb connect 192.168.1.100:5555

# Instalar apk
adb install app.apk

# Desinstalar app
adb uninstall com.package.name

# Ejecutar comando shell
adb shell comando

# Obtener nivel de bateria
adb shell dumpsys battery

# Obtener almacenamiento
adb shell df /data

# Tomar screenshot
adb exec-out screencap -p > screenshot.png

# Limpiar datos de app
adb shell pm clear com.package.name
```

---

## Seguridad

### Buenas Practicas

- El archivo .env contiene datos sensibles - NO COMPARTIR
- La carpeta venv/ no se versiona - NO COMMITEAR
- La carpeta node_modules/ no se versiona
- Usar HTTPS en produccion
- Validar tokens en endpoints sensibles

### .gitignore Recomendado

```
venv/
node_modules/
.env
.DS_Store
__pycache__/
*.pyc
build/
dist/
*.log
.idea/
.vscode/
```



## Despliegue 


