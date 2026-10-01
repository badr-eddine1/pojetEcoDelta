
FROM mcr.microsoft.com/playwright/python:v1.62.0-jammy

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Ce conteneur n'expose aucun port : surveillance.py tourne en boucle, pas un serveur web
CMD ["python", "surveillance.py"]
