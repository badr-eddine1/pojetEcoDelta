
FROM python:3.12-slim

WORKDIR /app

# Dépendances système minimales (psycopg2 a besoin de libpq)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Le dossier uploads (images produits) doit survivre aux redéploiements -> monté en volume
RUN mkdir -p uploads

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
