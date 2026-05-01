"""
utils.py - Utilidades
Funciones auxiliares para logging, variables de entorno y gestión de archivos.
"""

import os
import logging
from datetime import datetime
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()


def get_env_variable(key, default=None):
    """
    Obtiene una variable de entorno.
    
    Args:
        key (str): Nombre de la variable.
        default: Valor por defecto si no existe.
        
    Returns:
        str: Valor de la variable o default.
    """
    return os.getenv(key, default)


def ensure_directories(directories):
    """
    Crea directorios si no existen.
    
    Args:
        directories (list): Lista de rutas de directorios.
    """
    for directory in directories:
        if not os.path.exists(directory):
            try:
                os.makedirs(directory)
            except OSError:
                pass


def setup_logging():
    """
    Configura el sistema de logging.
    
    Returns:
        logging.Logger: Logger configurado.
    """
    # Asegurar que la carpeta logs existe
    ensure_directories(['./logs'])
    
    # Nombre del archivo de log
    log_filename = f"./logs/execution_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    
    # Crear logger
    logger = logging.getLogger('AutomationBot')
    logger.setLevel(logging.DEBUG)
    
    # Handler para archivo
    file_handler = logging.FileHandler(log_filename, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    
    # Handler para consola
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # Formato
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # Agregar handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger


def log_message(logger, level, message):
    """
    Registra un mensaje con el nivel especificado.
    
    Args:
        logger: Logger a usar.
        level (str): Nivel de log (INFO, WARN, ERROR, DEBUG).
        message (str): Mensaje a registrar.
    """
    level = level.upper()
    
    if level == "INFO":
        logger.info(message)
    elif level == "WARN" or level == "WARNING":
        logger.warning(message)
    elif level == "ERROR":
        logger.error(message)
    elif level == "DEBUG":
        logger.debug(message)
    else:
        logger.info(message)


def parse_device_list(adb_output):
    """
    Parsea la salida de 'adb devices' para extraer seriales.
    
    Args:
        adb_output (str): Output de 'adb devices'.
        
    Returns:
        list: Lista de seriales de dispositivos.
    """
    devices = []
    lines = adb_output.strip().split('\n')[1:]  # Saltar primera línea
    
    for line in lines:
        line = line.strip()
        if line and 'device' in line and 'offline' not in line:
            parts = line.split()
            if parts:
                devices.append(parts[0])
    
    return devices
