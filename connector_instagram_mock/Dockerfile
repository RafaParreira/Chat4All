FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Agora funciona, pois o arquivo está no contexto raiz:
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY connector_instagram_mock /app

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8003"]
