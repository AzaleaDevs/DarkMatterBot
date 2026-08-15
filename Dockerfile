FROM python:3.10-slim

# Fuente usada por el comando /meme. Pillow incluye sus librerias nativas.
RUN apt-get update && apt-get install -y --no-install-recommends \
    fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copiar SOLO requirements primero
COPY requirements.txt .

# Instalar pip deps (solo si cambias requirements)
RUN pip install --no-cache-dir -r requirements.txt

# Copiar todo el proyecto
COPY . .

CMD ["python", "main.py"]
