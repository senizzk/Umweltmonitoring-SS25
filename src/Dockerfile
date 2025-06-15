# Verwende ein offizielles Python-Laufzeit-Image als Basis
FROM python:3.10-slim

# Setze das Arbeitsverzeichnis im Container
WORKDIR /app

# Kopiere die requirements.txt-Datei in das Arbeitsverzeichnis
COPY requirements.txt .

# Installiere alle benötigten Python-Pakete aus der requirements.txt
# --no-cache-dir: reduziert die Image-Größe
# --trusted-host: vermeidet SSL-Probleme in bestimmten Netzwerken
RUN pip install --no-cache-dir --trusted-host pypi.python.org -r requirements.txt

# Kopiere den restlichen Code (z. B. main_app.py, sensor_utils.py) in den Container
COPY . .

# Öffne Port 8050 für den Zugriff von außen
EXPOSE 8050

# Starte die Anwendung beim Hochfahren des Containers
CMD ["python", "app.py"]
