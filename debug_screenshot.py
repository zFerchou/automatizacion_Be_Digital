"""
debug_screenshot.py - Debuggear screenshots
Prueba tomar screenshot y convertirlo
"""

import subprocess
import os
from datetime import datetime

def debug_screenshot():
    """Debuggea screenshots"""
    
    print("="*70)
    print("🔍 DEBUG DE SCREENSHOTS")
    print("="*70)
    
    # 1. Verificar dispositivos
    print("\n1️⃣ LISTAR DISPOSITIVOS:")
    try:
        devices_output = subprocess.check_output(["adb", "devices"], text=True)
        print(devices_output)
    except Exception as e:
        print(f"Error: {e}")
        return
    
    # Obtener primer dispositivo
    lines = devices_output.strip().split("\n")[1:]
    devices = []
    for line in lines:
        line = line.strip()
        if line and "device" in line and "offline" not in line:
            serial = line.split()[0]
            devices.append(serial)
    
    if not devices:
        print("❌ No hay dispositivos conectados")
        return
    
    device = devices[0]
    print(f"\n✅ Dispositivo seleccionado: {device}")
    
    # 2. Verificar Pillow
    print("\n2️⃣ VERIFICAR PILLOW:")
    try:
        from PIL import Image
        print("✅ Pillow instalado correctamente")
    except ImportError:
        print("❌ Pillow NO está instalado")
        print("   Ejecuta: pip install Pillow")
        return
    
    # 3. Crear carpeta outputs
    print("\n3️⃣ CREAR CARPETA OUTPUTS:")
    os.makedirs('./outputs', exist_ok=True)
    print("✅ Carpeta outputs lista")
    
    # 4. Tomar screenshot
    print(f"\n4️⃣ TOMAR SCREENSHOT de {device}:")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    png_filename = f"screenshot_{device}_{timestamp}_temp.png"
    png_filepath = os.path.join('./outputs', png_filename)
    
    try:
        print(f"   Guardando PNG temporal: {png_filepath}")
        result = subprocess.run([
            "adb", "-s", device,
            "exec-out", "screencap", "-p"
        ], capture_output=True)
        
        if result.returncode == 0:
            with open(png_filepath, 'wb') as f:
                f.write(result.stdout)
            
            file_size = os.path.getsize(png_filepath)
            print(f"✅ PNG guardado: {file_size} bytes")
            print(f"   Ubicación: {png_filepath}")
        else:
            print(f"❌ Error en ADB: {result.stderr.decode()}")
            return
    except Exception as e:
        print(f"❌ Error: {e}")
        return
    
    # 5. Convertir a JPG
    print(f"\n5️⃣ CONVERTIR PNG A JPG:")
    try:
        print("   Abriendo PNG...")
        img = Image.open(png_filepath)
        print(f"   ✅ PNG abierto correctamente")
        print(f"   Tamaño: {img.size}")
        print(f"   Modo: {img.mode}")
        
        jpg_filename = f"screenshot_{device}_{timestamp}.jpg"
        jpg_filepath = os.path.join('./outputs', jpg_filename)
        
        print(f"   Guardando JPG: {jpg_filepath}")
        
        # Convertir a RGB si es necesario
        if img.mode in ('RGBA', 'LA', 'P'):
            print("   Convertiendo a RGB...")
            rgb_img = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'RGBA':
                rgb_img.paste(img, mask=img.split()[-1])
            else:
                rgb_img.paste(img)
            rgb_img.save(jpg_filepath, 'JPEG', quality=95)
        else:
            img.save(jpg_filepath, 'JPEG', quality=95)
        
        jpg_size = os.path.getsize(jpg_filepath)
        print(f"✅ JPG guardado: {jpg_size} bytes")
        print(f"   Ubicación: {jpg_filepath}")
        
        # Eliminar PNG temporal
        print("\n6️⃣ ELIMINAR PNG TEMPORAL:")
        try:
            os.remove(png_filepath)
            print(f"✅ PNG temporal eliminado")
        except Exception as e:
            print(f"⚠️  No se pudo eliminar PNG: {e}")
        
    except Exception as e:
        print(f"❌ Error en conversión: {e}")
        return
    
    # 7. Verificar archivo final
    print("\n7️⃣ VERIFICAR ARCHIVO FINAL:")
    if os.path.exists(jpg_filepath):
        size = os.path.getsize(jpg_filepath)
        print(f"✅ Archivo existe: {jpg_filepath}")
        print(f"   Tamaño: {size} bytes")
        print(f"\n✅ PUEDES ABRIR ESTA IMAGEN EN WINDOWS FOTOS")
    else:
        print(f"❌ Archivo no existe: {jpg_filepath}")
    
    print("\n" + "="*70)
    print("FIN DEL DEBUG")
    print("="*70)

if __name__ == "__main__":
    debug_screenshot()