"""
main.py - Orquestador Principal
Script que detecta dispositivos ADB y ejecuta tareas en paralelo usando threading.
Examen Práctico - Be Digital | Posición: Líder de Proyecto
"""

import subprocess
import threading
import os
import sys
from datetime import datetime
from device_bot import DeviceBot
from utils import setup_logging, log_message

# Configurar logging
logger = setup_logging()

class DeviceManager:
    """Gestor de dispositivos ADB con ejecución paralela."""
    
    def __init__(self):
        self.devices = []
        self.threads = []
        self.lock = threading.Lock()
        
    def detect_devices(self):
        """
        Detecta todos los dispositivos conectados vía ADB.
        
        Returns:
            list: Lista de seriales de dispositivos detectados.
        """
        try:
            result = subprocess.check_output(["adb", "devices"], text=True)
            lines = result.strip().split("\n")[1:]  # Saltar la primera línea
            
            devices = []
            for line in lines:
                line = line.strip()
                if line and "device" in line and "offline" not in line and "emulator" not in line.lower():
                    # Formato: "serial device" o "emulator-5554 device"
                    serial = line.split()[0]
                    if serial:
                        devices.append(serial)
            
            self.devices = devices
            return devices
            
        except FileNotFoundError:
            log_message(logger, "ERROR", "ADB no está instalado o no está en PATH")
            return []
        except subprocess.CalledProcessError as e:
            log_message(logger, "ERROR", f"Error al ejecutar adb: {str(e)}")
            return []
    
    def execute_on_device(self, device_serial):
        """
        Ejecuta la tarea en un dispositivo específico.
        Diseñado para ejecutarse en un hilo separado.
        
        Args:
            device_serial (str): Serial del dispositivo Android.
        """
        bot = DeviceBot(device_serial)
        
        try:
            log_message(logger, "INFO", f"[{device_serial}] Iniciando ejecución...")
            
            # 1. Verificar conectividad
            if not bot.is_device_connected():
                log_message(logger, "ERROR", f"[{device_serial}] Dispositivo no accesible")
                return
            
            # 2. Abrir aplicación de Configuración
            log_message(logger, "INFO", f"[{device_serial}] Abriendo app de Configuración...")
            bot.open_settings_app()
            
            # 3. Leer batería
            battery = bot.get_battery_level()
            log_message(logger, "INFO", f"[{device_serial}] Batería: {battery}%")
            
            # 4. Leer almacenamiento
            storage = bot.get_storage_info()
            log_message(logger, "INFO", f"[{device_serial}] Almacenamiento disponible: {storage['available']}MB ({storage['percentage']}%)")
            
            # 5. Tomar screenshot si almacenamiento < 10%
            screenshot_taken = False
            if storage['percentage'] < 10:
                log_message(logger, "WARN", f"[{device_serial}]  Almacenamiento bajo ({storage['percentage']}%). Tomando screenshot...")
                bot.take_screenshot()
                screenshot_taken = True
            
            # 6. Crear payload JSON y enviar
            payload = bot.create_payload(battery, storage, screenshot_taken)
            log_message(logger, "INFO", f"[{device_serial}] Payload creado: {payload}")
            
            # 7. Enviar a endpoint API
            api_response = bot.send_to_api(payload)
            if api_response:
                log_message(logger, "INFO", f"[{device_serial}] ✅ Datos enviados a API exitosamente")
            
            # 8. Guardar en archivo local
            bot.save_to_file(payload)
            log_message(logger, "INFO", f"[{device_serial}] ✅ Datos guardados en archivo local")
            
            log_message(logger, "INFO", f"[{device_serial}] ✅ Tarea completada exitosamente")
            
        except Exception as e:
            log_message(logger, "ERROR", f"[{device_serial}] Excepción durante ejecución: {str(e)}")
    
    def run_parallel(self):
        """
        Ejecuta la tarea en todos los dispositivos detectados de forma simultánea.
        Utiliza threading para paralelismo.
        """
        if not self.devices:
            log_message(logger, "WARN", "No se detectaron dispositivos conectados")
            return False
        
        log_message(logger, "INFO", f" Ejecutando en {len(self.devices)} dispositivo(s): {', '.join(self.devices)}")
        
        # Crear un hilo por dispositivo
        self.threads = []
        for device_serial in self.devices:
            thread = threading.Thread(
                target=self.execute_on_device,
                args=(device_serial,),
                name=f"DeviceThread-{device_serial}"
            )
            thread.daemon = False
            self.threads.append(thread)
            thread.start()
        
        # Esperar a que todos los hilos terminen
        for thread in self.threads:
            thread.join()
        
        log_message(logger, "INFO", "✅ Todas las tareas paralelas completadas")
        return True


def main():
    """Función principal."""
    print("\n" + "="*70)
    print("    🤖 AUTOMATIZACIÓN PARALELA DE DISPOSITIVOS ANDROID - Be Digital")
    print("="*70 + "\n")
    
    log_message(logger, "INFO", "Iniciando script de automatización...")
    
    # Crear gestor de dispositivos
    manager = DeviceManager()
    
    # Detectar dispositivos
    print("📱 Detectando dispositivos conectados...\n")
    devices = manager.detect_devices()
    
    if not devices:
        print("❌ No se encontraron dispositivos conectados.")
        print("\nVerifica:")
        print("  1. Conecta el dispositivo/emulador")
        print("  2. Ejecuta 'adb devices' en terminal")
        print("  3. Autoriza la depuración USB en el dispositivo")
        log_message(logger, "ERROR", "Proceso abortado: No hay dispositivos")
        sys.exit(1)
    
    print(f"✅ Se encontraron {len(devices)} dispositivo(s):\n")
    for i, device in enumerate(devices, 1):
        print(f"   {i}. {device}")
    print()
    
    # Ejecutar en paralelo
    if manager.run_parallel():
        print("\n" + "="*70)
        print("    ✅ EJECUCIÓN COMPLETADA EXITOSAMENTE")
        print("="*70)
        print("\n Archivos guardados en:")
        print("   - Logs: ./logs/execution.log")
        print("   - Datos: ./outputs/device_*.txt")
        print("\n")
    else:
        print("\n" + "="*70)
        print("    ❌ LA EJECUCIÓN FALLÓ")
        print("="*70 + "\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
