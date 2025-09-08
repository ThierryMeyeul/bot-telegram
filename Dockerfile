# Dockerfile pour Koyeb
FROM python:3.12-slim

# Crée le dossier de l'app
WORKDIR /app

# Copie requirements et installe
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copie le reste du projet
COPY . .

# Commande pour lancer le bot
CMD ["python", "main.py"]
