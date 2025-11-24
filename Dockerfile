FROM python:3.10-slim

# Dependencias del sistema
RUN apt-get update && apt-get install -y \
    libjpeg62-turbo-dev \
    zlib1g-dev \
    libfreetype6 \
    libfreetype6-dev \
    liblcms2-dev \
    libopenjp2-7-dev \
    libharfbuzz-dev \
    libtiff6 \
    libwebp-dev \
    libpng-dev \
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
