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
        Versión mejorada con mejor manejo de errores y debugging.
        
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
            
            if not output:
                print(f"[DEBUG {self.device_serial}] No output from df command")
                return {
                    'total': 0,
                    'used': 0,
                    'available': 0,
                    'percentage': 0,
                    'raw': "No output from df command"
                }
            
            print(f"[DEBUG {self.device_serial}] Output crudo de df: {repr(output)}")
            
            lines = output.strip().split("\n")
            print(f"[DEBUG {self.device_serial}] Total de líneas: {len(lines)}")
            
            # Android puede devolver 2 o más líneas
            # Línea 0: Header (Filesystem Size Used Available Use% Mounted)
            # Línea 1: Datos (/data XXXX YYYY ZZZZ XX% /data)
            
            if len(lines) >= 2:
                # Obtener la línea de datos (puede ser línea 1 o última)
                data_line = None
                for i, line in enumerate(lines[1:], 1):
                    print(f"[DEBUG {self.device_serial}] Línea {i}: {repr(line)}")
                    if "/data" in line:
                        data_line = line
                        break
                
                if not data_line:
                    data_line = lines[-1]
                    print(f"[DEBUG {self.device_serial}] Usando última línea: {repr(data_line)}")
                
                parts = data_line.split()
                print(f"[DEBUG {self.device_serial}] Parts parseados: {parts}")
                print(f"[DEBUG {self.device_serial}] Cantidad de partes: {len(parts)}")
                
                if len(parts) >= 4:
                    try:
                        # Intentar formato: Filesystem Size Used Available Use% Mounted
                        # Index:           0         1    2    3         4    5
                        
                        total_blocks = int(parts[1])
                        used_blocks = int(parts[2])
                        available_blocks = int(parts[3])
                        
                        print(f"[DEBUG {self.device_serial}] Bloques parseados:")
                        print(f"[DEBUG {self.device_serial}]   Total: {total_blocks}")
                        print(f"[DEBUG {self.device_serial}]   Usado: {used_blocks}")
                        print(f"[DEBUG {self.device_serial}]   Disponible: {available_blocks}")
                        
                        # Convertir bloques (1K cada uno) a MB
                        total_mb = total_blocks // 1024
                        used_mb = used_blocks // 1024
                        available_mb = available_blocks // 1024
                        
                        # Evitar división por cero
                        if total_mb > 0:
                            percentage = (available_mb / total_mb) * 100
                        else:
                            percentage = 0
                        
                        print(f"[DEBUG {self.device_serial}] Convertido a MB:")
                        print(f"[DEBUG {self.device_serial}]   Total: {total_mb}MB")
                        print(f"[DEBUG {self.device_serial}]   Usado: {used_mb}MB")
                        print(f"[DEBUG {self.device_serial}]   Disponible: {available_mb}MB")
                        print(f"[DEBUG {self.device_serial}]   % Libre: {percentage:.2f}%")
                        
                        return {
                            'total': total_mb,
                            'used': used_mb,
                            'available': available_mb,
                            'percentage': round(percentage, 2),
                            'raw': output
                        }
                    except (ValueError, IndexError) as e:
                        print(f"[DEBUG {self.device_serial}] Error en formato 1: {e}")
                        # Si falla, intentar índices alternativos
                        try:
                            # Alternativa: los índices podrían ser 0, 1, 2
                            total_blocks = int(parts[0])
                            used_blocks = int(parts[1])
                            available_blocks = int(parts[2])
                            
                            print(f"[DEBUG {self.device_serial}] Intentando formato alternativo...")
                            print(f"[DEBUG {self.device_serial}]   Total: {total_blocks}")
                            print(f"[DEBUG {self.device_serial}]   Usado: {used_blocks}")
                            print(f"[DEBUG {self.device_serial}]   Disponible: {available_blocks}")
                            
                            total_mb = total_blocks // 1024
                            used_mb = used_blocks // 1024
                            available_mb = available_blocks // 1024
                            
                            if total_mb > 0:
                                percentage = (available_mb / total_mb) * 100
                            else:
                                percentage = 0
                            
                            return {
                                'total': total_mb,
                                'used': used_mb,
                                'available': available_mb,
                                'percentage': round(percentage, 2),
                                'raw': output
                            }
                        except Exception as e2:
                            print(f"[DEBUG {self.device_serial}] Error en formato alternativo: {e2}")
                else:
                    print(f"[DEBUG {self.device_serial}] No hay suficientes partes: {len(parts)}")
            else:
                print(f"[DEBUG {self.device_serial}] No hay suficientes líneas: {len(lines)}")
            
            return {
                'total': 0,
                'used': 0,
                'available': 0,
                'percentage': 0,
                'raw': output or "No data available"
            }
        
        except Exception as e:
            print(f"[DEBUG {self.device_serial}] Exception general: {e}")
            return {
                'total': 0,
                'used': 0,
                'available': 0,
                'percentage': 0,
                'raw': str(e)
            }
    
    def take_screenshot(self):
        """
        Toma un screenshot del dispositivo cuando el almacenamiento es bajo.
        El archivo se guarda en el directorio output como JPG (compatible con Windows).
        
        Returns:
            str: Ruta del archivo screenshot, o None si falla.
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Primero guardar como PNG temporal
            png_filename = f"screenshot_{self.device_serial}_{timestamp}_temp.png"
            png_filepath = os.path.join(self.output_folder, png_filename)
            
            # Tomar screenshot usando subprocess.run
            result = subprocess.run([
                "adb", "-s", self.device_serial,
                "exec-out", "screencap", "-p"
            ], capture_output=True)
            
            if result.returncode != 0:
                print(f"[ERROR] ADB screencap falló: {result.stderr}")
                return None
            
            # Guardar PNG
            with open(png_filepath, 'wb') as f:
                f.write(result.stdout)
            
            # Convertir a JPG (compatible con Windows)
            try:
                from PIL import Image
                
                # Abrir PNG
                img = Image.open(png_filepath)
                
                # Guardar como JPG
                jpg_filename = f"screenshot_{self.device_serial}_{timestamp}.jpg"
                jpg_filepath = os.path.join(self.output_folder, jpg_filename)
                
                # Convertir a RGB si es necesario
                if img.mode in ('RGBA', 'LA', 'P'):
                    rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'RGBA':
                        rgb_img.paste(img, mask=img.split()[-1])
                    else:
                        rgb_img.paste(img)
                    rgb_img.save(jpg_filepath, 'JPEG', quality=95)
                else:
                    img.save(jpg_filepath, 'JPEG', quality=95)
                
                # Eliminar PNG temporal
                try:
                    os.remove(png_filepath)
                except:
                    pass
                
                return jpg_filepath
            except ImportError:
                # Si no está PIL, devolver PNG
                print(f"[ADVERTENCIA] PIL no instalado. Screenshot guardado como PNG")
                return png_filepath
            except Exception as e:
                print(f"[ERROR] Conversión a JPG: {e}")
                return png_filepath
                
        except Exception as e:
            print(f"[ERROR] Al tomar screenshot: {e}")
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
            "timestamp_iso": datetime.now().isoformat(),
            "timestamp_legible": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            "bateria": {
                "porcentaje": battery,
                "unidad": "%"
            },
            "almacenamiento": {
                "total_mb": storage['total'],
                "usado_mb": storage.get('used', 0),
                "disponible_mb": storage['available'],
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