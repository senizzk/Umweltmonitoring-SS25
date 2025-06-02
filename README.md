## 🌤️ Umweltmonitoring für Moste

### 📷 Beispielansicht

![Dashboard Screenshot](./assets/dashboard.jpg)

---


## 📌 Projektüberblick

Das Ziel dieses Projekts ist die Entwicklung eines webbasierten Dashboards zur Überwachung und Vorhersage von Umweltdaten, das mit einer frei gewählten **senseBox** verbunden ist.

Die Anwendung stellt aktuelle Sensordaten sowie Prognosen für Temperatur und Niederschlag visuell dar und speichert darüber hinaus eine umfangreiche Historie zur Analyse vergangener Messwerte.

---

### 🧱 Systemarchitektur

Das Dashboard basiert auf drei Hauptkomponenten:

- **Datenquelle:**  
  Integration einer senseBox über die offizielle **senseBox API** zur Erfassung von Umweltdaten  
  *(z. B. Temperatur, Luftfeuchtigkeit, Luftdruck, Feinstaub)*

- **Datenhaltung:**  
  Speicherung von bis zu **10.000 Zeitreihendatenpunkten** in einer **PostgreSQL-Datenbank mit TimescaleDB-Erweiterung**,  
  um historische Analysen und maschinelles Lernen zu ermöglichen.

- **Visualisierung:**  
  Darstellung der aktuellen Messwerte sowie historischer Entwicklungen in einem interaktiven Dashboard  
  mit **Plotly**, eingebunden in eine **React**-Anwendung.

---

### 🧠 Maschinelles Lernen

- Implementierung eines **Machine-Learning-Moduls mit Facebook Prophet**  
- **Tägliche Erstellung einer 7-Tage-Vorhersage** für Temperatur und Niederschlagsmenge  
- **Prognose basiert auf lokal gespeicherten Zeitreihendaten** (PostgreSQL/TimescaleDB)

---

### 🔁 Echtzeitfunktionen

- Automatische **Aktualisierung alle 3 Minuten**: Neue Sensordaten werden regelmäßig abgerufen und im Dashboard angezeigt  
- Die **letzte Aktualisierungszeit** ist stets im Interface sichtbar  
- **Wettervorhersage-Daten werden alle 24 Stunden** neu berechnet

---

### 🌤️ Zusätzliche Funktionen

- **Dynamische Wetter-Icons** basierend auf der prognostizierten Niederschlagsmenge  
- Anzeige von **PM2.5 / PM10 Feinstaubwerten** in µg/m³  
- **Sonnenaufgang und Sonnenuntergang** für den aktuellen Tag  
- **7-Tage-Wetterübersicht** mit Höchst- und Tiefstwerten

