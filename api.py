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
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        return sys.executable
    
    venv_paths = [
        os.path.join(os.getcwd(), 'venv', 'Scripts', 'python.exe'),
        os.path.join(os.getcwd(), 'venv', 'Scripts', 'python'),
        os.path.join(os.getcwd(), 'venv', 'bin', 'python'),
        os.path.join(os.getcwd(), 'venv', 'bin', 'python3'),
    ]
    
    for venv_python in venv_paths:
        if os.path.exists(venv_python):
            print(f"[API] Usando Python del venv: {venv_python}")
            return venv_python
    
    print(f"[API] Usando Python actual: {sys.executable}")
    return sys.executable

def parse_devices_from_files():
    """
    Lee y parsea los archivos device_*.txt
    Retorna lista de dispositivos con datos mas recientes
    SOLO retorna dispositivos cuyo ULTIMO estado NO es 'desconectado'
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
                                            if data.get('estado') != 'desconectado':
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

    disconnected = set(prev_devices) - set(current_devices)
    for device_id in disconnected:
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
                f.write(f"\n{json.dumps(disconnect_event, ensure_ascii=False, indent=2)}\n")
            print(f"[API] Dispositivo {device_id} marcado como desconectado.")
        except Exception as e:
            print(f"[API] Error registrando desconexion de {device_id}: {e}")

    try:
        with open(CONNECTED_DEVICES_FILE, 'w', encoding='utf-8') as f:
            json.dump(current_devices, f)
    except Exception as e:
        print(f"[API] Error guardando estado de dispositivos: {e}")

@app.route('/api/devices', methods=['GET'])
def get_devices():
    """Obtiene SOLO dispositivos CONECTADOS"""
    devices = parse_devices_from_files()
    
    for device in devices:
        device_id = device.get('id_dispositivo', '')
        device['screenshots'] = get_screenshots_for_device(device_id)
    
    print(f"[API] Dispositivos conectados: {len(devices)}")
    return jsonify(devices)

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
    """Obtiene historico"""
    history = []
    try:
        if os.path.exists('./outputs'):
            for file in os.listdir('./outputs'):
                if file.startswith('device_') and file.endswith('.txt'):
                    filepath = os.path.join('./outputs', file)
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                        json_blocks = re.findall(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', content, re.DOTALL)
                        for json_str in json_blocks:
                            try:
                                data = json.loads(json_str)
                                if data.get('estado') == 'desconectado' and data.get('mensaje'):
                                    data['isDisconnectLog'] = True
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

@app.route('/api/logs', methods=['GET'])
def get_logs():
    """
    Obtiene las ultimas lineas del log de ejecucion.
    """
    try:
        log_file = './logs/execution.log'
        if os.path.exists(log_file):
            with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
                lines = [line.strip() for line in lines if line.strip()]
                
                errors = [l for l in lines if 'ERROR' in l]
                warnings = [l for l in lines if 'WARNING' in l or 'WARN' in l]
                
                return jsonify({
                    'status': 'success',
                    'logs': lines,
                    'total_lines': len(lines),
                    'errors': errors,
                    'warnings': warnings,
                    'filename': 'execution.log'
                })
        return jsonify({
            'status': 'success',
            'logs': ['Archivo de log no encontrado. Ejecute primero.'],
            'total_lines': 1,
            'errors': [],
            'warnings': [],
            'filename': 'execution.log'
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'logs': [f'Error al leer logs: {str(e)}'],
            'total_lines': 1,
            'errors': [str(e)],
            'warnings': []
        })

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
        print(f"[API] Existe: {os.path.exists(main_py_path)}")
        
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        result = subprocess.run(
            [python_exe, main_py_path],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='ignore',
            timeout=300,
            cwd=current_dir,
            env=env
        )
        
        print("[API] main.py completado")
        print(f"[API] Return code: {result.returncode}")
        
        # SOBRESCRIBIR el log para mostrar solo la ejecucion actual
        os.makedirs('./logs', exist_ok=True)
        with open('./logs/execution.log', 'w', encoding='utf-8') as f:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            f.write(f"{'='*70}\n")
            f.write(f"EJECUCION: {timestamp}\n")
            f.write(f"{'='*70}\n\n")
            
            if result.stdout:
                f.write("--- SALIDA DEL SCRIPT ---\n")
                f.write(result.stdout.strip() + "\n\n")
            
            if result.stderr:
                f.write("--- LOGS DEL SISTEMA ---\n")
                f.write(result.stderr.strip() + "\n\n")
            
            f.write(f"{'='*70}\n")
            f.write(f"FIN EJECUCION (codigo: {result.returncode})\n")
            f.write(f"{'='*70}\n")
        
        if result.stdout:
            print(f"[API] Output: {result.stdout[-300:]}")
        if result.stderr:
            print(f"[API] Stderr: {result.stderr[-300:]}")
        
        time.sleep(2)
        
        devices = parse_devices_from_files()
        current_device_ids = [d.get('id_dispositivo') for d in devices if d.get('id_dispositivo')]
        update_device_connection_status(current_device_ids)
        
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
        print("[API] ERROR: Timeout")
        return jsonify({
            'status': 'error',
            'message': 'Timeout al ejecutar main.py'
        }), 408
    except Exception as e:
        print(f"[API] ERROR: {e}")
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
    """Sirve archivos estaticos"""
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
    print("   GET  /api/logs")
    print("   POST /api/run-main")
    print("   GET  /api/screenshot/<filename>")
    print("\nPresiona Ctrl+C para detener")
    print("="*70 + "\n")
    
    app.run(debug=False, port=5000, threaded=True)