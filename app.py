import os
import subprocess
import threading
import time
import requests
from flask import Flask

app = Flask(__name__)

# 🔴 PEGA AQUÍ TODAS TUS URLs DIRECTAS DE LA NUBE EN ORDEN
# Asegúrate de separarlas por comas y envolverlas en comillas
LISTA_VIDEOS = [
    "https://gamma.videonest.org/4381d6c7-8b1d-4a27-9cd3-cfa32e3d67ab_video_v2.mp4",
    "https://gamma.videonest.org/4381d6c7-8b1d-4a27-9cd3-cfa32e3d67ab_video_v2.mp4",
    "https://gamma.videonest.org/4381d6c7-8b1d-4a27-9cd3-cfa32e3d67ab_video_v2.mp4"
]

RTMP_URL = os.environ.get("RTMP_URL")

def stream_playlist():
    if not RTMP_URL:
        print("ERROR: La variable de entorno RTMP_URL no está configurada.")
        return

    if not LISTA_VIDEOS:
        print("ERROR: La lista de videos está vacía.")
        return

    # Comando FFmpeg configurado para recibir datos continuos desde la tubería (pipe:0)
    ffmpeg_cmd = [
        'ffmpeg',
        '-f', 'mp4',            # Indica que los datos entrantes por el pipe son formato MP4
        '-i', 'pipe:0',         # Lee la entrada estándar generada por Python
        '-c:v', 'libx264',
        '-preset', 'veryfast',
        '-b:v', '1500k',
        '-maxrate', '1500k',
        '-bufsize', '3000k',
        '-pix_fmt', 'yuv420p',
        '-g', '50',
        '-c:a', 'aac',
        '-b:a', '128k',
        '-ar', '44100',
        '-f', 'flv',            # Formato de salida para SSH101
        RTMP_URL
    ]

    print("Iniciando FFmpeg en modo continuo...")
    # Iniciamos FFmpeg esperando datos por stdin
    ffmpeg_process = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

    # Hilo secundario para leer los logs de FFmpeg y ver errores en la consola de Render
    def log_reader():
        for line in ffmpeg_process.stdout:
            print(line, end='')
    threading.Thread(target=log_reader, daemon=True).start()

    # Bucle infinito para recorrer la lista de videos una y otra vez
    while True:
        for url in LISTA_VIDEOS:
            print(f"Transmitiendo ahora: {url}")
            try:
                # Descarga el video en fragmentos pequeños (stream=True) para no saturar la RAM de Render
                with requests.get(url, stream=True, timeout=30) as response:
                    response.raise_for_status()
                    for chunk in response.iter_content(chunk_size=4096):
                        if ffmpeg_process.poll() is not None:
                            print("FFmpeg se detuvo inesperadamente. Reiniciando proceso...")
                            return # Sale de la función para que el script principal lo reinicie completo
                        
                        # Inyecta los bytes del video directamente en el motor de FFmpeg
                        ffmpeg_process.stdin.write(chunk)
            except Exception as e:
                print(f"Error al leer el video {url}: {e}. Pasando al siguiente video...")
                time.sleep(2) # Espera breve antes de continuar si un enlace falla
        
        print("Lista completada. Reiniciando lista de reproducción...")

def manage_stream_lifecycle():
    while True:
        stream_playlist()
        print("Reiniciando el ciclo de transmisión en 5 segundos...")
        time.sleep(5)

@app.route('/')
def home():
    return f"Transmisor continuo activo. Total de videos en lista: {len(LISTA_VIDEOS)}", 200

if __name__ == "__main__":
    # Inicia el ciclo vital de la transmisión en segundo plano
    threading.Thread(target=manage_stream_lifecycle, daemon=True).start()
    
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
