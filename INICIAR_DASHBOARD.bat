@echo off
REM Script para iniciar el Dashboard completo en Windows

echo.
echo ======================================================================
echo     INICIANDO DASHBOARD COMPLETO - Be Digital
echo ======================================================================
echo.

REM Verificar si Node.js está instalado
where node >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo  Node.js no está instalado
    echo    Descarga desde: https://nodejs.org/
    pause
    exit /b 1
)

REM Verificar si Python está instalado
where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo  Python no está instalado
    pause
    exit /b 1
)

echo  Node.js detectado
echo  Python detectado
echo.

REM Verificar si package.json existe
if not exist "package.json" (
    echo  package.json no encontrado
    echo    Asegúrate de estar en la carpeta correcta
    pause
    exit /b 1
)

echo  Instalando dependencias de React...
call npm install
if %ERRORLEVEL% NEQ 0 (
    echo  Error en npm install
    pause
    exit /b 1
)

echo  Dependencias instaladas

echo.
echo  Compilando React (npm run build)...
call npm run build
if %ERRORLEVEL% NEQ 0 (
    echo  Error en build
    pause
    exit /b 1
)

echo  React compilado
echo.

REM Instalar Flask-CORS si no está
pip install flask-cors >nul 2>nul

echo.
echo ======================================================================
echo     SETUP COMPLETADO - Iniciando servicios...
echo ======================================================================
echo.

echo Se abrirán 2 ventanas de terminal:
echo   1. Terminal 1: Backend Flask (api.py)
echo   2. Terminal 2: Frontend React (npm start)
echo.
echo El navegador se abrirá automáticamente en: http://localhost:3000
echo.
echo Presiona Enter para continuar...
pause

REM Abrir Terminal 1: api.py
start "Terminal 1 - api.py" cmd /k python api.py

REM Esperar un segundo
timeout /t 1 /nobreak

REM Abrir Terminal 2: npm start
start "Terminal 2 - React" cmd /k npm start

echo.
echo ======================================================================
echo     TODO INICIADO - Abre: http://localhost:3000
echo ======================================================================
echo.
