import subprocess
import threading
import os
import sys
from datetime import datetime
from device_bot import DeviceBot
from utils import setup_logging, log_message

logger = setup_logging()

class DeviceManager:
    """Gestor de dispositivos ADB con ejecución paralela."""
    
    def __init__(self):
        self.devices = []
        self.threads = []
        self.results = []  # Almacenar resultados de cada hilo
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
                # Aceptar TANTO dispositivos físicos COMO emuladores
                if line and "device" in line and "offline" not in line:
                    # Formato serial device
                    serial = line.split()[0]
                    if serial:
                        devices.append(serial)
            
            self.devices = devices
            log_message(logger, "INFO", f"Dispositivos detectados: {len(devices)} - {', '.join(devices) if devices else 'Ninguno'}")
            return devices
            
        except FileNotFoundError:
            log_message(logger, "ERROR", "ADB no está instalado o no está en PATH")
            return []
        except subprocess.CalledProcessError as e:
            log_message(logger, "ERROR", f"Error al ejecutar adb: {str(e)}")
            return []
    
    def verify_device_connection(self, device_serial):
        """
        Verifica que el dispositivo siga conectado durante la ejecución.
        
        Args:
            device_serial (str): Serial del dispositivo
            
        Returns:
            bool: True si está conectado, False si no
        """
        try:
            result = subprocess.run(
                ['adb', '-s', device_serial, 'shell', 'echo', 'ok'],
                capture_output=True,
                text=True,
                timeout=5
            )
            is_connected = result.returncode == 0 and 'ok' in result.stdout
            
            if not is_connected:
                log_message(logger, "ERROR", f"[{device_serial}]  DISPOSITIVO DESCONECTADO - No responde a ADB")
            
            return is_connected
            
        except subprocess.TimeoutExpired:
            log_message(logger, "ERROR", f"[{device_serial}]  TIMEOUT - Dispositivo no responde")
            return False
        except Exception as e:
            log_message(logger, "ERROR", f"[{device_serial}]  Error verificando conexión: {str(e)}")
            return False
    
    def execute_on_device(self, device_serial):
        """
        Ejecuta la tarea en un dispositivo específico.
        Diseñado para ejecutarse en un hilo separado.
        
        Args:
            device_serial (str): Serial del dispositivo Android.
        """
        bot = DeviceBot(device_serial)
        max_retries = 3
        retry_count = 0
        
        try:
            log_message(logger, "INFO", f"[{device_serial}] Iniciando ejecución...")
            
            # Verificar conectividad inicial (con reintentos)
            while retry_count < max_retries:
                if bot.is_device_connected():
                    log_message(logger, "INFO", f"[{device_serial}] ✅ Dispositivo conectado y accesible")
                    break
                else:
                    retry_count += 1
                    if retry_count < max_retries:
                        log_message(logger, "WARNING", f"[{device_serial}]  Intento {retry_count}/{max_retries} - Dispositivo no accesible, reintentando...")
                        import time
                        time.sleep(2)
                    else:
                        log_message(logger, "ERROR", f"[{device_serial}]  DISPOSITIVO NO ACCESIBLE después de {max_retries} intentos")
                        with self.lock:
                            self.results.append({
                                'id_dispositivo': device_serial,
                                'estado': 'error',
                                'error': 'Dispositivo no accesible',
                                'timestamp': datetime.now().isoformat()
                            })
                        return
            
            # 2. Abrir aplicación de Configuración
            log_message(logger, "INFO", f"[{device_serial}] Abriendo app de Configuración...")
            if not self.verify_device_connection(device_serial):
                raise ConnectionError("Dispositivo desconectado durante la ejecución")
            
            app_opened = bot.open_settings_app()
            if app_opened:
                log_message(logger, "INFO", f"[{device_serial}] ✅ App abierta: com.android.settings")
            else:
                log_message(logger, "WARNING", f"[{device_serial}]  No se pudo abrir la app de Configuración")
            
            # 3. Leer batería
            log_message(logger, "INFO", f"[{device_serial}] Leyendo nivel de batería...")
            if not self.verify_device_connection(device_serial):
                raise ConnectionError("Dispositivo desconectado durante la ejecución")
            
            battery = bot.get_battery_level()
            log_message(logger, "INFO", f"[{device_serial}] Batería: {battery}%")
            
            # 4. Leer almacenamiento
            log_message(logger, "INFO", f"[{device_serial}] Leyendo almacenamiento...")
            if not self.verify_device_connection(device_serial):
                raise ConnectionError("Dispositivo desconectado durante la ejecución")
            
            storage = bot.get_storage_info()
            log_message(logger, "INFO", f"[{device_serial}] Almacenamiento: {storage['available']}MB disponible ({storage['percentage']}% libre)")
            
            # 5. Tomar screenshot si almacenamiento < 10%
            screenshot_taken = False
            if storage['percentage'] < 10:
                log_message(logger, "WARNING", f"[{device_serial}]  ALMACENAMIENTO BAJO ({storage['percentage']}%). Tomando screenshot...")
                if not self.verify_device_connection(device_serial):
                    raise ConnectionError("Dispositivo desconectado durante la ejecución")
                bot.take_screenshot()
                screenshot_taken = True
                log_message(logger, "INFO", f"[{device_serial}] 📸 Screenshot tomado por almacenamiento bajo")
            else:
                log_message(logger, "INFO", f"[{device_serial}] Almacenamiento suficiente ({storage['percentage']}%), no se requiere screenshot")
            
            # 6. Crear payload JSON
            payload = bot.create_payload(battery, storage, screenshot_taken)
            log_message(logger, "INFO", f"[{device_serial}] Payload creado correctamente")
            
            # 7. Enviar a endpoint API
            if not self.verify_device_connection(device_serial):
                raise ConnectionError("Dispositivo desconectado durante la ejecución")
            
            api_response = bot.send_to_api(payload)
            if api_response:
                log_message(logger, "INFO", f"[{device_serial}] ✅ Datos enviados a API exitosamente")
            else:
                log_message(logger, "WARNING", f"[{device_serial}]  No se pudo enviar a API, guardando localmente")
            
            # 8. Guardar en archivo local
            bot.save_to_file(payload)
            log_message(logger, "INFO", f"[{device_serial}] ✅ Datos guardados en archivo local")
            
            # Éxito
            log_message(logger, "INFO", f"[{device_serial}] ✅ TAREA COMPLETADA EXITOSAMENTE")
            
            with self.lock:
                self.results.append({
                    'id_dispositivo': device_serial,
                    'estado': 'completado',
                    'battery': battery,
                    'storage': storage,
                    'screenshot_taken': screenshot_taken,
                    'timestamp': datetime.now().isoformat()
                })
            
        except ConnectionError as e:
            log_message(logger, "ERROR", f"[{device_serial}]  DESCONECTADO: {str(e)}")
            with self.lock:
                self.results.append({
                    'id_dispositivo': device_serial,
                    'estado': 'desconectado',
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                })
        except Exception as e:
            log_message(logger, "ERROR", f"[{device_serial}]  ERROR: {str(e)}")
            with self.lock:
                self.results.append({
                    'id_dispositivo': device_serial,
                    'estado': 'error',
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                })
    
    def run_parallel(self):
        """
        Ejecuta la tarea en todos los dispositivos detectados de forma simultánea.
        Utiliza threading para paralelismo.
        """
        if not self.devices:
            log_message(logger, "WARNING", "No se detectaron dispositivos conectados")
            return False
        
        log_message(logger, "INFO", "=" * 70)
        log_message(logger, "INFO", f" INICIANDO EJECUCIÓN PARALELA EN {len(self.devices)} DISPOSITIVO(S)")
        log_message(logger, "INFO", f"   Dispositivos: {', '.join(self.devices)}")
        log_message(logger, "INFO", "=" * 70)
        
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
            log_message(logger, "INFO", f"Hilo iniciado para dispositivo: {device_serial}")
        
        # Esperar a que todos los hilos terminen
        for thread in self.threads:
            thread.join()
        
        # Resumen de ejecución
        log_message(logger, "INFO", "=" * 70)
        log_message(logger, "INFO", "RESUMEN DE EJECUCIÓN:")
        
        completados = [r for r in self.results if r['estado'] == 'completado']
        errores = [r for r in self.results if r['estado'] == 'error']
        desconectados = [r for r in self.results if r['estado'] == 'desconectado']
        
        log_message(logger, "INFO", f"   ✅ Completados: {len(completados)}")
        for r in completados:
            log_message(logger, "INFO", f"      - {r['id_dispositivo']}: Batería {r.get('battery', 'N/A')}%, Almacenamiento {r.get('storage', {}).get('percentage', 'N/A')}%")
        
        if desconectados:
            log_message(logger, "ERROR", f"    Desconectados: {len(desconectados)}")
            for r in desconectados:
                log_message(logger, "ERROR", f"      - {r['id_dispositivo']}: {r['error']}")
        
        if errores:
            log_message(logger, "ERROR", f"    Errores: {len(errores)}")
            for r in errores:
                log_message(logger, "ERROR", f"      - {r['id_dispositivo']}: {r['error']}")
        
        log_message(logger, "INFO", "=" * 70)
        log_message(logger, "INFO", "✅ Todas las tareas paralelas completadas")
        
        return True


def main():
    """Función principal."""
    print("\n" + "="*70)
    print("     AUTOMATIZACIÓN PARALELA DE DISPOSITIVOS ANDROID - Be Digital")
    print("="*70 + "\n")
    
    log_message(logger, "INFO", "Iniciando script de automatización...")
    
    # Crear gestor de dispositivos
    manager = DeviceManager()
    
    # Detectar dispositivos
    print(" Detectando dispositivos conectados...\n")
    devices = manager.detect_devices()
    
    if not devices:
        print(" No se encontraron dispositivos conectados.")
        print("\nVerifica:")
        print("  1. Conecta el dispositivo/emulador por USB")
        print("  2. Ejecuta 'adb devices' en terminal")
        print("  3. Autoriza la depuración USB en el dispositivo")
        print("  4. Asegúrate que no esté 'offline'")
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
        print("     LA EJECUCIÓN FALLÓ")
        print("="*70 + "\n")
        sys.exit(1)


if __name__ == "__main__":
    main()