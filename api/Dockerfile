FROM python:3.11-slim

WORKDIR /app

# Instala dependências do sistema necessárias para 'cryptography'
RUN apt-get update && apt-get install -y build-essential libffi-dev && rm -rf /var/lib/apt/lists/*

# Copia e instala dependências do Python
COPY ./requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o restante do código
COPY . /app

# Expõe a porta e roda a API
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
