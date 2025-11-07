# worker/Dockerfile
FROM python:3.11-slim

# Diretório de trabalho
WORKDIR /app

# (Opcional, mas deixa tudo mais tranquilo com libs nativas)
# - libpq-dev: útil p/ Postgres (psycopg2)
# - gcc: caso alguma dependência precise compilar algo
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copia as dependências do worker
# IMPORTANTE: mantenha um requirements.txt DENTRO de ./worker
COPY ./requirements.txt .

# Instala as dependências do worker
# (usa psycopg2-binary + confluent-kafka do seu requirements)
RUN pip install --no-cache-dir -r requirements.txt

# Copia o código do worker
COPY . .

# Comando para iniciar o consumer
CMD ["python", "consumer.py"]
