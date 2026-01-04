# Dockerfile
FROM python:3.11-slim

# Evita prompts interativos
ENV DEBIAN_FRONTEND=noninteractive

# Instala FFmpeg e dependências do sistema
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsm6 \
    libxext6 \
    libgl1-mesa-glx \
    fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Define diretório de trabalho
WORKDIR /app

# Copia requirements primeiro (melhor cache)
COPY requirements.txt .

# Instala dependências Python
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copia o resto do código
COPY . .

# Cria pastas necessárias
RUN mkdir -p output/videos output/audio output/images output/projects output/shorts output/logs

# Define variável de ambiente para Python não bufferizar output
ENV PYTHONUNBUFFERED=1

# Comando para iniciar o bot
CMD ["python", "bot.py"]