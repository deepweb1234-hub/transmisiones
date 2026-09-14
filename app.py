import os
import subprocess
import threading
from flask import Flask

app = Flask(__name__)

# Configuración básica
VIDEO_FILE = "video.mp4"  # Coloca tu video con este nombre exacto en la raíz de tu proyecto
# La URL RTMP se toma de las variables de entorno de Render
RTMP_URL = os.environ.get("RTMP_URL")

def start_streaming():
    if not RTMP_URL:
        print("ERROR: La variable de entorno RTMP_URL no está configurada.")
        return

    if not os.path.exists(VIDEO_FILE):
        print(f"ERROR: No se encontró el archivo {VIDEO_FILE} en la raíz de la aplicación.")
        return

    # Comando FFmpeg optimizado para los límites de Render Free (512MB RAM / CPU compartida)
    ffmpeg_cmd = [
        'ffmpeg',
        '-re',                  # Lee el archivo en tiempo real simulando una captura en vivo
        '-stream_loop', '-1',   # Hace que el video se repita infinitamente en bucle
        '-i', VIDEO_FILE,       # Archivo MP4 de entrada
        '-c:v', 'libx264',      # Codec H.264 altamente compatible
        '-preset', 'veryfast',  # Compresión rápida para no saturar la CPU gratuita de Render
        '-b:v', '2000k',        # Bitrate de video limitado para estabilidad en redes virtuales
        '-maxrate', '2000k',
        '-bufsize', '4000k',
        '-pix_fmt', 'yuv420p',  # Formato de color estándar para streaming
        '-g', '50',             # Intervalo de fotogramas clave (Keyframes) regular
        '-c:a', 'aac',          # Codec de audio AAC estándar
        '-b:a', '128k',         # Calidad de audio balanceada
        '-ar', '44100',         # Frecuencia de muestreo estándar
        '-f', 'flv',            # Formato contenedor FLV requerido por RTMP
        RTMP_URL                # Dirección y clave destino (YouTube, Twitch, etc.)
    ]

    print("Iniciando transmisión RTMP...")
    process = subprocess.Popen(ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    
    # Redirige los logs de FFmpeg directamente a la consola de Render para monitoreo
    for line in process.stdout:
        print(line, end='')

@app.route('/')
def home():
    return "¡Streamer de video activo! Para transmisiones 24/7 sin interrupciones, conecta un monitor HTTP externo.", 200

if __name__ == "__main__":
    # Inicia el proceso de streaming en un hilo secundario para evitar bloquear a Flask
    stream_thread = threading.Thread(target=start_streaming, daemon=True)
    stream_thread.start()
    
    # Toma el puerto asignado dinámicamente por la infraestructura de Render
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
