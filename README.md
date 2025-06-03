## 🌤️ Umweltmonitoring für Moste


![Dashboard Screenshot](./assets/dashboard.jpg)

---


## 📌 Projektüberblick

Das Ziel dieses Projekts ist die Entwicklung eines webbasierten Dashboards zur Überwachung und Vorhersage von Umweltdaten, das mit einem **senseBox** verbunden ist.

Die Anwendung stellt aktuelle Sensordaten sowie Prognosen für Temperatur und Niederschlag visuell dar.



### 🧱 Systemarchitektur

Das Dashboard basiert auf drei Hauptkomponenten:

- **Datenquelle:**  
  Integration einer senseBox über die **senseBox API** zur Erfassung von Umweltdaten  
  *(z. B. Temperatur, Luftfeuchtigkeit, Luftdruck, Feinstaub)*

- **Datenhaltung:**  
  Speicherung von  **10.000 Zeitreihendatenpunkten** in einer **PostgreSQL-Datenbank mit TimescaleDB-Erweiterung**,  
  um historische Analysen und maschinelles Lernen zu ermöglichen.

- **Visualisierung:**  
  Darstellung der aktuellen Messwerte sowie historischer Entwicklungen in einem interaktiven Dashboard  
  mit **Plotly Dash**.



## 🧠 Besondere Merkmale


- Wetterdaten wie Temperatur, Luftfeuchtigkeit und Niederschlag werden **alle 3 Minuten automatisch** abgerufen und im Dashboard angezeigt. Am unteren Rand der Seite wird ein Countdown bis zum nächsten Update eingeblendet.

<img src="./assets/countdown.jpg" alt="countdown" width="40%"/>


- Ein **Machine-Learning-Modul mit Facebook Prophet** wurde implementiert,  
  um auf Basis historischer Wetterdaten **tägliche Durchschnittswerte für den Niederschlag sowie minimale und maximale Temperaturwerte** vorherzusagen.

<img src="./assets/prophet.jpg" alt="prophet" width="40%"/>


- Die historischen Wetterdaten (Temperatur und Niederschlag), die als Trainingsdaten für das Machine-Learning-Modell dienen, werden **alle 24 Stunden automatisch** neu abgerufen. Das Modell wird anschließend mit den aktualisierten Daten automatisch neu trainiert.

![update](./assets/modelupdate.jpg)


- Die Wetter-Icons im Dashboard **ändern sich** je nach vorhergesagter Niederschlagsmenge.

![icons](./assets/icons.jpg)





