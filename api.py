"""
api.py - Backend Flask DEFINITIVO
Ejecuta main.py correctamente y sirve screenshots
"""

from flask import Flask, jsonify, send_from_directory, send_file
from flask_cors import CORS
import json
import os
import sys
from datetime import datetime
import re
import subprocess
import time
import tempfile

app = Flask(__name__)
CORS(app)

app.static_folder = 'build'
app.static_url_path = ''

def get_python_executable():
    """
    Obtiene el path al ejecutable de Python (del venv si existe)
    """
    # Si estamos en un venv, usar ese Python
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        return sys.executable
    
    # Buscar python en venv
    venv_paths = [
        os.path.join(os.getcwd(), 'venv', 'Scripts', 'python.exe'),  # Windows
        os.path.join(os.getcwd(), 'venv', 'Scripts', 'python'),      # Windows alt
        os.path.join(os.getcwd(), 'venv', 'bin', 'python'),          # Linux/Mac
        os.path.join(os.getcwd(), 'venv', 'bin', 'python3'),         # Linux/Mac alt
    ]
    
    for venv_python in venv_paths:
        if os.path.exists(venv_python):
            print(f"[API] Usando Python del venv: {venv_python}")
            return venv_python
    
    # Si no encuentra venv, usar el actual
    print(f"[API] Usando Python actual: {sys.executable}")
    return sys.executable

def parse_devices_from_files():
    """
    Lee y parsea los archivos device_*.txt
    Retorna lista de dispositivos con datos más recientes
    """
    devices = []
    
    try:
        if os.path.exists('./outputs'):
            for file in os.listdir('./outputs'):
                if file.startswith('device_') and file.endswith('.txt'):
                    filepath = os.path.join('./outputs', file)
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            content = f.read()
                            json_blocks = re.findall(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', content, re.DOTALL)
                            
                            if json_blocks:
                                for json_str in reversed(json_blocks):
                                    try:
                                        data = json.loads(json_str)
                                        if 'id_dispositivo' in data:
                                            devices.append(data)
                                            break
                                    except json.JSONDecodeError:
                                        continue
                    except Exception as e:
                        print(f"Error leyendo {file}: {e}")
    except Exception as e:
        print(f"Error en parse_devices: {e}")
    
    return devices

def get_screenshots_for_device(device_id):
    """
    Obtiene lista de screenshots para un dispositivo
    """
    screenshots = []
    
    try:
        if os.path.exists('./outputs'):
            for file in os.listdir('./outputs'):
                if file.startswith(f'screenshot_{device_id}') and (file.endswith('.jpg') or file.endswith('.png')):
                    screenshots.append(file)
    except:
        pass
    
    # Ordenar por más reciente primero
    screenshots.sort(reverse=True)
    return screenshots

CONNECTED_DEVICES_FILE = os.path.join(tempfile.gettempdir(), 'connected_devices.json')

def update_device_connection_status(current_devices):
    """
    Compara los dispositivos actuales con los previamente conectados y registra desconexiones.
    """
    prev_devices = []
    if os.path.exists(CONNECTED_DEVICES_FILE):
        try:
            with open(CONNECTED_DEVICES_FILE, 'r', encoding='utf-8') as f:
                prev_devices = json.load(f)
        except Exception as e:
            print(f"[API] Error leyendo estado previo de dispositivos: {e}")

    # Dispositivos desconectados
    disconnected = set(prev_devices) - set(current_devices)
    for device_id in disconnected:
        # Registrar evento de desconexión en el archivo correspondiente
        file_path = os.path.join('./outputs', f'device_{device_id}.txt')
        timestamp = datetime.now().isoformat()
        timestamp_legible = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
        disconnect_event = {
            "id_dispositivo": device_id,
            "timestamp_iso": timestamp,
            "timestamp_legible": timestamp_legible,
            "estado": "desconectado",
            "mensaje": f"Dispositivo {device_id} desconectado"
        }
        try:
            with open(file_path, 'a', encoding='utf-8') as f:
                f.write(f"\n=== DESCONEXIÓN ===\n{json.dumps(disconnect_event, ensure_ascii=False, indent=2)}\n")
            print(f"[API] Dispositivo {device_id} marcado como desconectado.")
        except Exception as e:
            print(f"[API] Error registrando desconexión de {device_id}: {e}")

    # Guardar el nuevo estado
    try:
        with open(CONNECTED_DEVICES_FILE, 'w', encoding='utf-8') as f:
            json.dump(current_devices, f)
    except Exception as e:
        print(f"[API] Error guardando estado de dispositivos: {e}")

@app.route('/api/devices', methods=['GET'])
def get_devices():
    """Obtiene dispositivos actuales y desconectados"""
    devices = parse_devices_from_files()
    # Obtener todos los device_ids que han existido
    all_device_ids = set()
    device_map = {}
    for device in devices:
        device_id = device.get('id_dispositivo')
        if device_id:
            all_device_ids.add(device_id)
            # Guardar el último estado conocido
            device_map[device_id] = device
    # Leer el registro de desconexiones
    import tempfile
    CONNECTED_DEVICES_FILE = os.path.join(tempfile.gettempdir(), 'connected_devices.json')
    prev_devices = []
    if os.path.exists(CONNECTED_DEVICES_FILE):
        try:
            with open(CONNECTED_DEVICES_FILE, 'r', encoding='utf-8') as f:
                prev_devices = json.load(f)
        except Exception as e:
            print(f"[API] Error leyendo estado previo de dispositivos: {e}")
        for device_id in prev_devices:
            all_device_ids.add(device_id)
    # Construir la lista final
    result = []
    for device_id in all_device_ids:
        device = device_map.get(device_id)
        if device:
            # Si tiene estado desconectado, lo dejamos así
            result.append(device)
        else:
            # Buscar el archivo y obtener el último evento
            file_path = os.path.join('./outputs', f'device_{device_id}.txt')
            last_data = None
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    json_blocks = re.findall(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', content, re.DOTALL)
                    for json_str in reversed(json_blocks):
                        try:
                            data = json.loads(json_str)
                            if data.get('id_dispositivo') == device_id:
                                last_data = data
                                break
                        except Exception:
                            continue
            if last_data:
                last_data['estado'] = 'desconectado'
                result.append(last_data)
            else:
                # Si no hay datos, crear uno básico
                result.append({
                    'id_dispositivo': device_id,
                    'estado': 'desconectado',
                    'timestamp_legible': '',
                })
    print(f"[API] Dispositivos encontrados (incluyendo desconectados): {len(result)}")
    return jsonify(result)

@app.route('/api/status', methods=['GET'])
def get_status():
    """Obtiene estado"""
    devices_count = 0
    total_executions = 0
    
    try:
        devices_count = len(parse_devices_from_files())
        if os.path.exists('./logs'):
            total_executions = len([f for f in os.listdir('./logs') if f.endswith('.log')])
    except:
        pass
    
    return jsonify({
        'timestamp': datetime.now().isoformat(),
        'dispositivos_conectados': devices_count,
        'total_ejecuciones': total_executions,
        'estado': 'activo'
    })

@app.route('/api/history', methods=['GET'])
def get_history():
    """Obtiene histórico"""
    history = []
    try:
        if os.path.exists('./outputs'):
            for file in os.listdir('./outputs'):
                if file.startswith('device_') and file.endswith('.txt'):
                    filepath = os.path.join('./outputs', file)
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                        # Buscar bloques JSON y también logs de desconexión
                        json_blocks = re.findall(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', content, re.DOTALL)
                        for json_str in json_blocks:
                            try:
                                data = json.loads(json_str)
                                # Buscar si es un evento de desconexión
                                if data.get('estado') == 'desconectado' and data.get('mensaje'):
                                    data['isDisconnectLog'] = True
                                # Agregar screenshots si existen
                                device_id = data.get('id_dispositivo')
                                if device_id:
                                    data['screenshots'] = get_screenshots_for_device(device_id)
                                history.append(data)
                            except:
                                continue
    except Exception as e:
        print(f"Error en get_history: {e}")
    history.sort(key=lambda x: x.get('timestamp_iso', ''), reverse=True)
    return jsonify(history[:100])

@app.route('/api/run-main', methods=['POST'])
def run_main():
    """
    Ejecuta main.py usando el Python correcto
    """
    try:
        print("\n[API] ========================================")
        print("[API] Ejecutando main.py...")
        print("[API] ========================================")
        
        current_dir = os.getcwd()
        main_py_path = os.path.join(current_dir, 'main.py')
        python_exe = get_python_executable()
        
        print(f"[API] Directorio: {current_dir}")
        print(f"[API] Python: {python_exe}")
        print(f"[API] main.py: {main_py_path}")
        print(f"[API] ¿Existe? {os.path.exists(main_py_path)}")
        
        # Ejecutar main.py con el Python del venv
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        result = subprocess.run(
            [python_exe, main_py_path],
            capture_output=True,
            text=True,
            timeout=300,
            cwd=current_dir,
            env=env
        )
        
        print("[API] main.py completado")
        print(f"[API] Return code: {result.returncode}")
        
        if result.stdout:
            print(f"[API] Output: {result.stdout[-300:]}")
        if result.stderr:
            print(f"[API] Stderr: {result.stderr[-300:]}")
        
        # Esperar a que se escriban los archivos
        time.sleep(2)
        
        # Leer datos NUEVOS
        devices = parse_devices_from_files()
        current_device_ids = [d.get('id_dispositivo') for d in devices if d.get('id_dispositivo')]
        update_device_connection_status(current_device_ids)
        
        # Agregar screenshots
        for device in devices:
            device_id = device.get('id_dispositivo', '')
            screenshots = get_screenshots_for_device(device_id)
            device['screenshots'] = screenshots
        
        print(f"[API] Dispositivos encontrados: {len(devices)}")
        
        return jsonify({
            'status': 'success' if result.returncode == 0 else 'error',
            'message': 'Ejecutado correctamente',
            'devices': devices,
            'returncode': result.returncode
        })
        
    except subprocess.TimeoutExpired:
        print("[API] ❌ ERROR: Timeout")
        return jsonify({
            'status': 'error',
            'message': 'Timeout al ejecutar main.py'
        }), 408
    except Exception as e:
        print(f"[API] ❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/screenshot/<filename>', methods=['GET'])
def get_screenshot(filename):
    """
    Sirve un screenshot
    """
    try:
        # Validar que el archivo existe y está en outputs
        filepath = os.path.join('./outputs', filename)
        if os.path.exists(filepath) and filename.startswith('screenshot_'):
            return send_file(filepath, mimetype='image/jpeg')
        else:
            return jsonify({'error': 'Screenshot no encontrado'}), 404
    except Exception as e:
        print(f"Error sirviendo screenshot: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health():
    """Health check"""
    devices = parse_devices_from_files()
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.now().isoformat(),
        'devices_found': len(devices),
        'python': get_python_executable()
    })

@app.route('/', methods=['GET'])
def index():
    """Sirve index.html"""
    try:
        return send_from_directory('build', 'index.html')
    except:
        return send_from_directory('build', 'index.html')

@app.route('/<path:path>', methods=['GET'])
def static_files(path):
    """Sirve archivos estáticos"""
    try:
        return send_from_directory('build', path)
    except:
        return send_from_directory('build', 'index.html')

if __name__ == '__main__':
    print("\n" + "="*70)
    print("    INICIANDO API - FLASK")
    print("="*70)
    print(f"\nPython usado: {get_python_executable()}")
    print("\nAbre en navegador:")
    print("   http://localhost:5000")
    print("\nEndpoints:")
    print("   GET  /api/devices")
    print("   GET  /api/status")
    print("   GET  /api/history")
    print("   POST /api/run-main")
    print("   GET  /api/screenshot/<filename>")
    print("\nPresiona Ctrl+C para detener")
    print("="*70 + "\n")
    
    app.run(debug=False, port=5000, threaded=True)