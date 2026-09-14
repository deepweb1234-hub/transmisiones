import os
import subprocess
import threading
import time
from flask import Flask

app = Flask(__name__)

# Lista secuencial de tus videos de Videonest (Asegúrate de que sean los links correctos)
LISTA_VIDEOS = [
    "https://gamma.videonest.org/8949c123-dd6a-431c-85d1-cc6cdeda2583_video_v5.mp4",
    "https://gamma.videonest.org/4381d6c7-8b1d-4a27-9cd3-cfa32e3d67ab_video_v2.mp4"
]

RTMP_URL = os.environ.get("RTMP_URL")

def start_streaming():
    if not RTMP_URL:
        print("ERROR CRÍTICO: La variable RTMP_URL no está definida.")
        return

    # Pequeña pausa inicial para garantizar que la red del contenedor esté lista
    time.sleep(5)

    while True:
        for video_url in LISTA_VIDEOS:
            print(f"Transmitiendo enlace en vivo: {video_url}")
            
            ffmpeg_cmd = [
                'ffmpeg',
                '-re',
                '-i', video_url,
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
                '-f', 'flv',
                RTMP_URL
            ]
            
            try:
                # El proceso corre el video actual de principio a fin
                process = subprocess.Popen(ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
                for line in process.stdout:
                    print(f"[FFmpeg OS] {line.strip()}")
                process.wait()
            except Exception as e:
                print(f"Fallo de conexión en hilo multimedia: {e}")
            
            time.sleep(3)

@app.route('/')
def home():
    return "Contenedor Docker-FFmpeg para la Iglesia CEMOA Activo.", 200

if __name__ == "__main__":
    threading.Thread(target=start_streaming, daemon=True).start()
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
