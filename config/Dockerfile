FROM python:3.9-slim

WORKDIR /app

# Installation des dépendances système
RUN apt-get update && apt-get install -y gcc g++ && rm -rf /var/lib/apt/lists/*

# Copie des fichiers
COPY requirements.txt .

# Installation avec numpy avant tout
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir numpy==1.22.4 && \
    pip install --no-cache-dir scikit-learn==1.1.3 && \
    pip install --no-cache-dir torch==1.13.1 --index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir transformers==4.25.1 && \
    pip install --no-cache-dir huggingface_hub==0.12.1 && \
    pip install --no-cache-dir sentence-transformers==2.2.2 && \
    pip install --no-cache-dir fastapi==0.95.2 uvicorn==0.22.0 && \
    pip install --no-cache-dir python-dotenv==1.0.0 loguru==0.7.0 pandas==1.5.3 && \
    pip install --no-cache-dir faiss-cpu==1.7.3 && \
    pip install --no-cache-dir pydantic==1.10.7

COPY . .

EXPOSE 8000

CMD ["uvicorn", "src.api.rest_api:app", "--host", "0.0.0.0", "--port", "8000"]
