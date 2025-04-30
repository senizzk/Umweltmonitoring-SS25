-- Aktiviert die TimescaleDB-Erweiterung (für Zeitreihendaten)
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Erstellt eine Tabelle für Sensordaten, falls sie noch nicht existiert
CREATE TABLE IF NOT EXISTS sensor_daten (
    zeitstempel TIMESTAMPTZ NOT NULL,     -- Zeitpunkt der Messung
    box_id TEXT NOT NULL,                 -- ID der SenseBox
    sensor_id TEXT NOT NULL,              -- ID des Sensors
    messwert DOUBLE PRECISION,            -- Gemessener Wert
    einheit TEXT,                         -- Einheit des Werts (z.B. °C, µg/m³)
    sensor_typ TEXT,                      -- Typ des Sensors (z.B. HDC1080)
    icon TEXT,                            -- Symboltyp (von der API)
    
    -- Verhindert doppelte Einträge (mehrfache gleiche Messung)
    UNIQUE (zeitstempel, box_id, sensor_id)
);

-- Konvertiert die Tabelle in eine sogenannte "Hypertable" für Zeitreihendaten
SELECT create_hypertable('sensor_daten', 'zeitstempel', if_not_exists => TRUE);

-- Tabelle für historische Verlaufsdaten
CREATE TABLE IF NOT EXISTS sensor_verlauf (
    zeitstempel TIMESTAMPTZ NOT NULL,
    box_id TEXT NOT NULL,
    sensor_id TEXT NOT NULL,
    messwert DOUBLE PRECISION,
    UNIQUE (zeitstempel, box_id, sensor_id)
);

-- Als Hypertable anlegen
SELECT create_hypertable('sensor_verlauf', 'zeitstempel', if_not_exists => TRUE);