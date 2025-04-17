import os
import requests
import pandas as pd
from sqlalchemy import create_engine, text

# Umgebungsvariablen (aus Docker Compose oder .env)
DB_USER = os.getenv("DB_USER", "gruppeeins")
DB_PASSWORD = os.getenv("DB_PASSWORD", "mypassword")
DB_HOST = os.getenv("DB_HOST", "db")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "umwelt_db")

# SenseBox-ID (von OpenSenseMap)
SENSEBOX_ID = os.getenv("SENSEBOX_ID", "6039fe0f2c4a41001be3726e")

# Verbindung zur TimescaleDB aufbauen
db_url = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(db_url)

def daten_von_api_holen(box_id=SENSEBOX_ID):
    """
    Holt aktuelle Sensordaten von der OpenSenseMap API.
    """
    url = f"https://api.opensensemap.org/boxes/{box_id}?format=json"
    response = requests.get(url)
    response.raise_for_status()
    inhalt = response.json()

    sensoren = inhalt.get("sensors", [])
    if not sensoren:
        print("⚠️ Keine Sensoren gefunden.")
        return None

    df = pd.json_normalize(sensoren)

    # Benötigte Felder extrahieren und umbenennen
    df['zeitstempel'] = pd.to_datetime(df['lastMeasurement.createdAt'], errors='coerce')
    df['messwert'] = pd.to_numeric(df['lastMeasurement.value'], errors='coerce')

    df_umgewandelt = df[[
        'zeitstempel',
        '_id',
        'messwert',
        'unit',
        'sensorType',
        'icon'
    ]].rename(columns={
        '_id': 'sensor_id',
        'unit': 'einheit',
        'sensorType': 'sensor_typ'
    })

    df_umgewandelt.dropna(subset=['zeitstempel', 'messwert'], inplace=True)

    return df_umgewandelt

def daten_in_datenbank_schreiben(df, box_id=SENSEBOX_ID):
    """
    Schreibt die verarbeiteten Sensordaten in die Datenbank (vermeidet Duplikate).
    """
    if df is None or df.empty:
        print("⚠️ Keine Daten zum Einfügen.")
        return

    with engine.begin() as conn:
        for _, zeile in df.iterrows():
            conn.execute(text("""
                INSERT INTO sensor_daten (
                    zeitstempel, box_id, sensor_id, messwert,
                    einheit, sensor_typ, icon
                ) VALUES (
                    :zeitstempel, :box_id, :sensor_id, :messwert,
                    :einheit, :sensor_typ, :icon
                )
                ON CONFLICT (zeitstempel, box_id, sensor_id) DO NOTHING;
            """), {
                "zeitstempel": zeile["zeitstempel"],
                "box_id": box_id,
                "sensor_id": zeile["sensor_id"],
                "messwert": zeile["messwert"],
                "einheit": zeile["einheit"],
                "sensor_typ": zeile["sensor_typ"],
                "icon": zeile["icon"]
            })
