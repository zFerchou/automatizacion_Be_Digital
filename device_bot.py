"""
device_bot.py - Robot de Dispositivo
Clase que encapsula toda la lógica ADB para un dispositivo individual.
"""

import subprocess
import re
import json
import os
from datetime import datetime
import requests
from utils import get_env_variable, ensure_directories


class DeviceBot:
    """Bot que ejecuta acciones en un dispositivo Android específico."""
    
    def __init__(self, device_serial):
        """
        Inicializa el bot para un dispositivo.
        
        Args:
            device_serial (str): Serial del dispositivo Android.
        """
        self.device_serial = device_serial
        self.settings_app = "com.android.settings"
        self.api_endpoint = get_env_variable("API_ENDPOINT")
        self.output_folder = get_env_variable("OUTPUT_FOLDER", "./outputs")
        ensure_directories([self.output_folder])
    
    def run_adb_command(self, command):
        """
        Ejecuta un comando ADB en el dispositivo.
        
        Args:
            command (list): Comando a ejecutar (ej: ["adb", "shell", "dumpsys", "battery"])
            
        Returns:
            str: Output del comando o None si falla.
        """
        try:
            # Inyectar device serial si no está incluido
            if "-s" not in command:
                command = ["adb", "-s", self.device_serial] + command[1:] if command[0] == "adb" else ["adb", "-s", self.device_serial] + command
            
            result = subprocess.check_output(command, text=True, stderr=subprocess.DEVNULL)
            return result.strip()
        except subprocess.CalledProcessError:
            return None
        except Exception as e:
            return None
    
    def is_device_connected(self):
        """
        Verifica si el dispositivo está conectado y accesible.
        
        Returns:
            bool: True si está conectado, False si no.
        """
        try:
            result = subprocess.check_output(["adb", "devices"], text=True)
            return self.device_serial in result and "offline" not in result
        except:
            return False
    
    def open_settings_app(self):
        """
        Abre la aplicación de Configuración en el dispositivo.
        
        Returns:
            bool: True si se abrió exitosamente.
        """
        try:
            command = [
                "adb", "-s", self.device_serial,
                "shell", "am", "start", "-n",
                f"{self.settings_app}/.Settings"
            ]
            subprocess.check_output(command, stderr=subprocess.DEVNULL)
            return True
        except:
            return False
    
    def get_battery_level(self):
        """
        Obtiene el nivel de batería actual del dispositivo.
        
        Returns:
            int: Porcentaje de batería (0-100), o -1 si hay error.
        """
        try:
            output = self.run_adb_command([
                "adb", "shell", "dumpsys", "battery"
            ])
            
            if output:
                # Buscar la línea "level: X"
                match = re.search(r'level:\s*(\d+)', output)
                if match:
                    return int(match.group(1))
            
            return -1
        except:
            return -1
    
    def get_storage_info(self):
        """
        Obtiene información de almacenamiento del dispositivo.
        
        Returns:
            dict: {
                'total': int (MB),
                'used': int (MB),
                'available': int (MB),
                'percentage': float (% disponible)
            }
        """
        try:
            output = self.run_adb_command([
                "adb", "shell", "df", "/data"
            ])
            
            if output:
                lines = output.strip().split("\n")
                if len(lines) >= 2:
                    # Formato típico:
                    # Filesystem    Size    Used Available Use% Mounted on
                    # /data        XXXXX   YYYY  ZZZZZ     XX% /data
                    
                    parts = lines[-1].split()
                    if len(parts) >= 3:
                        try:
                            # Convertir de bloques a MB (cada bloque = 1K)
                            available_blocks = int(parts[2])
                            available_mb = available_blocks // 1024
                            
                            # Calcular porcentaje (simplificado)
                            total_blocks = int(parts[0])
                            total_mb = total_blocks // 1024
                            
                            percentage = (available_mb / total_mb * 100) if total_mb > 0 else 0
                            
                            return {
                                'total': total_mb,
                                'available': available_mb,
                                'percentage': round(percentage, 2),
                                'raw': output
                            }
                        except (ValueError, IndexError):
                            pass
            
            return {
                'total': 0,
                'available': 0,
                'percentage': 0,
                'raw': output or "Error al parsear"
            }
        except Exception as e:
            return {
                'total': 0,
                'available': 0,
                'percentage': 0,
                'raw': str(e)
            }
    
    def take_screenshot(self):
        """
        Toma un screenshot del dispositivo cuando el almacenamiento es bajo.
        El archivo se guarda en el directorio output.
        
        Returns:
            str: Ruta del archivo screenshot, o None si falla.
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"screenshot_{self.device_serial}_{timestamp}.png"
            filepath = os.path.join(self.output_folder, filename)
            
            # Tomar screenshot y enviarlo a la PC
            subprocess.check_output([
                "adb", "-s", self.device_serial,
                "exec-out", "screencap", "-p"
            ], stderr=subprocess.DEVNULL, stdout=open(filepath, 'wb'))
            
            return filepath
        except:
            return None
    
    def create_payload(self, battery, storage, screenshot_taken=False):
        """
        Crea el payload JSON con los datos recolectados.
        
        Args:
            battery (int): Nivel de batería.
            storage (dict): Información de almacenamiento.
            screenshot_taken (bool): Si se tomó screenshot.
            
        Returns:
            dict: Payload estructurado en JSON.
        """
        payload = {
            "id_dispositivo": self.device_serial,
            "timestamp": datetime.now().isoformat(),
            "bateria": {
                "porcentaje": battery,
                "unidad": "%"
            },
            "almacenamiento": {
                "disponible_mb": storage['available'],
                "total_mb": storage['total'],
                "porcentaje_libre": storage['percentage'],
                "unidad": "MB"
            },
            "acciones": {
                "app_abierta": self.settings_app,
                "screenshot_tomado": screenshot_taken,
                "almacenamiento_bajo": storage['percentage'] < 10
            }
        }
        return payload
    
    def send_to_api(self, payload):
        """
        Envía los datos a un endpoint API.
        
        Args:
            payload (dict): Datos a enviar.
            
        Returns:
            bool: True si se envió exitosamente.
        """
        if not self.api_endpoint:
            return False
        
        try:
            headers = {"Content-Type": "application/json"}
            response = requests.post(
                self.api_endpoint,
                json=payload,
                headers=headers,
                timeout=10
            )
            return response.status_code in [200, 201, 202]
        except requests.exceptions.RequestException:
            return False
    
    def save_to_file(self, payload):
        """
        Guarda los datos en un archivo .txt local con id del dispositivo,
        fecha y hora.
        
        Args:
            payload (dict): Datos a guardar.
            
        Returns:
            str: Ruta del archivo creado, o None si falla.
        """
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d_%H:%M:%S")
            filename = f"device_{self.device_serial}.txt"
            filepath = os.path.join(self.output_folder, filename)
            
            # Leer datos anteriores si existen (para acumular)
            existing_data = []
            if os.path.exists(filepath):
                with open(filepath, 'r', encoding='utf-8') as f:
                    existing_data = f.readlines()
            
            # Agregar nueva entrada
            with open(filepath, 'a', encoding='utf-8') as f:
                f.write("="*70 + "\n")
                f.write(f"Timestamp: {timestamp}\n")
                f.write(f"ID Dispositivo: {self.device_serial}\n")
                f.write(f"JSON:\n{json.dumps(payload, indent=2, ensure_ascii=False)}\n\n")
            
            return filepath
        except Exception as e:
            return None
