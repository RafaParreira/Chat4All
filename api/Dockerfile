FROM python:3.11-slim

# Define diretório de trabalho
WORKDIR /app

# Instala dependências de sistema mínimas para compilar extensões Python
# (necessárias para psycopg2 e eventuais libs de Kafka)
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copia e instala dependências Python
COPY ./requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o código-fonte
COPY . /app

# Expõe a porta usada pela API
EXPOSE 8000

# Comando padrão para iniciar a API FastAPI
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
