import os
import subprocess
import threading
import time
from flask import Flask

app = Flask(__name__)


# ============================================================
# VIDEOS QUE SE VAN A TRANSMITIR
# ============================================================

LISTA_VIDEOS = [
    "https://live20.bozztv.com/giatvplayout/giatvvod/giatv/movies/playlist/212245/Intro1.mp4/playlist.m3u8",
]


# ============================================================
# RTMP DE SSH101 / BOZZTV
# ============================================================

RTMP_URL = os.environ.get("RTMP_URL")


# ============================================================
# TRANSMISIÓN
# ============================================================

def start_streaming():

    if not RTMP_URL:

        print(
            "ERROR CRÍTICO: "
            "La variable RTMP_URL no está definida."
        )

        return


    # Esperar a que la red esté disponible
    time.sleep(5)


    while True:

        for video_url in LISTA_VIDEOS:

            print()
            print("=" * 70)
            print("INICIANDO TRANSMISIÓN")
            print(video_url)
            print("=" * 70)
            print()


            # ====================================================
            # FFmpeg
            # ====================================================

            ffmpeg_cmd = [

                "ffmpeg",

                # -----------------------------------------------
                # LEER EL VIDEO A VELOCIDAD REAL
                # -----------------------------------------------

                "-re",

                # -----------------------------------------------
                # crear bucle
                # -----------------------------------------------
              
                "-stream_loop", "-1",

                # -----------------------------------------------
                # PARÁMETROS DE RECONEXIÓN SEGURA (EVITA BANEOS)
                # -----------------------------------------------
                "-reconnect", "1",
                "-reconnect_at_eof", "1",
                "-reconnect_streamed", "1",
                "-reconnect_delay_max", "3",
                

                # -----------------------------------------------
                # ENTRADA
                # -----------------------------------------------

                "-i",
                video_url,


                # =================================================
                # VIDEO
                # =================================================

                "-c:v",
                "libx264",

                # Menor consumo de CPU
                "-preset",
                "ultrafast",

                # Resolución
                "-vf",
                "scale=854:480",

                # Bitrate
                "-b:v",
                "800k",

                "-maxrate",
                "800k",

                "-bufsize",
                "1600k",

                # Compatibilidad
                "-pix_fmt",
                "yuv420p",


                # =================================================
                # KEYFRAMES
                # =================================================

                # 60 frames = 2 segundos si estamos a 30 FPS
                "-g",
                "60",

                "-keyint_min",
                "60",

                # Evitar keyframes variables
                "-sc_threshold",
                "0",

                # Forzar keyframe cada 2 segundos
                "-force_key_frames",
                "expr:gte(t,n_forced*2)",


                # =================================================
                # AUDIO
                # =================================================

                "-c:a",
                "aac",

                "-b:a",
                "64k",

                # 48 kHz es habitual para streaming
                "-ar",
                "48000",

                "-ac",
                "2",


                # =================================================
                # SALIDA RTMP
                # =================================================

                "-f",
                "flv",

                # Evitar metadatos de duración/tamaño
                "-flvflags",
                "no_duration_filesize",

                RTMP_URL
            ]


            try:

                print("Ejecutando FFmpeg...")


                process = subprocess.Popen(
                    ffmpeg_cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1
                )


                # =================================================
                # MOSTRAR LOG DE FFMPEG
                # =================================================

                for line in process.stdout:

                    line = line.strip()

                    if line:

                        print(
                            f"[FFmpeg] {line}"
                        )


                process.wait()


                print()
                print(
                    f"FFmpeg terminó con código: "
                    f"{process.returncode}"
                )


            except Exception as e:

                print()
                print(
                    "FALLO DE CONEXIÓN EN FFmpeg:"
                )

                print(e)


            # ====================================================
            # PAUSA ANTES DE SIGUIENTE VIDEO
            # ====================================================

            print(
                "Esperando 3 segundos antes "
                "de reiniciar la transmisión..."
            )

            time.sleep(3)


# ============================================================
# RUTA DE COMPROBACIÓN
# ============================================================

@app.route("/")
def home():

    return (
        "Contenedor Docker-FFmpeg "
        "para la Iglesia CEMOA Activo."
    ), 200


# ============================================================
# INICIO
# ============================================================

if __name__ == "__main__":

    threading.Thread(
        target=start_streaming,
        daemon=True
    ).start()


    port = int(
        os.environ.get(
            "PORT",
            10000
        )
    )


    app.run(
        host="0.0.0.0",
        port=port
    )
