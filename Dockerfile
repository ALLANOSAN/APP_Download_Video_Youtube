FROM python:3.11-slim
WORKDIR /app

# Instala ffmpeg e dependências do sistema
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Garante que a raiz do app esteja no PATH do Python para encontrar o módulo 'src'
ENV PYTHONPATH=/app

COPY requirements.txt .
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "src.server.main:app", "--host", "0.0.0.0", "--port", "8000"]