# Utiliza una imagen oficial de Python que ya incluye herramientas de compilación
FROM python:3.11-slim

# Instala FFmpeg de manera nativa con permisos de administrador en el contenedor
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

# Configura el directorio de trabajo interno
WORKDIR /app

# Copia e instala los requerimientos de Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia el resto del código del script al contenedor
COPY . .

# Expone el puerto que Render asignará dinámicamente
EXPOSE 10000

# Comando para arrancar el servidor de streaming
CMD ["python", "app.py"]
