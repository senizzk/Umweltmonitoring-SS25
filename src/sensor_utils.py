import os
import requests
import pandas as pd
from sqlalchemy import create_engine, text
from datetime import datetime, timedelta, timezone
from prophet import Prophet


# Umgebungsvariablen (aus Docker Compose oder .env)
DB_USER = os.getenv("DB_USER", "gruppeeins")
DB_PASSWORD = os.getenv("DB_PASSWORD", "mypassword")
DB_HOST = os.getenv("DB_HOST", "db")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "umwelt_db")

# SenseBox-ID (von OpenSenseMap)
SENSEBOX_ID = os.getenv("SENSEBOX_ID", "67a661af4ef45d0008682744")

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

    box_name = inhalt.get("name", "Unbekannt")
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
        'name': 'sensor_name',
        'unit': 'einheit',
        'sensorType': 'sensor_typ'
    })

    df_umgewandelt.dropna(subset=['zeitstempel', 'messwert'], inplace=True)

    return df_umgewandelt, box_name

def daten_in_datenbank_schreiben(df, box_id=SENSEBOX_ID, box_name="Unbekannt"):
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
                "sensor_name": box_name,
                "sensor_id": zeile["sensor_id"],
                "messwert": zeile["messwert"],
                "einheit": zeile["einheit"],
                "sensor_typ": zeile["sensor_typ"],
                "icon": zeile["icon"]
            })


def verlauf_daten_von_api_holen(sensor_id, box_id=SENSEBOX_ID, tage=10):
    """
    Holt historische Messwerte eines Sensors basierend auf dem letzten Messzeitpunkt,
    oder nutzt datetime.now() falls keiner vorhanden ist.
    """
    # 1. Box-Daten holen
    url_box = f"https://api.opensensemap.org/boxes/{box_id}?format=json"
    response = requests.get(url_box)
    response.raise_for_status()
    box_daten = response.json()

    # 2. Sensor finden
    sensoren = box_daten.get("sensors", [])
    sensor_info = next((s for s in sensoren if s["_id"] == sensor_id), None)

    # 3. Zeitbereich bestimmen
    if sensor_info and "lastMeasurement" in sensor_info:
        bis_datum = pd.to_datetime(sensor_info["lastMeasurement"]["createdAt"], utc=True)
    else:
        print("⚠️ Kein letzter Messwert gefunden – fallback to now()")
        bis_datum = datetime.now(timezone.utc)

    von_datum = bis_datum - timedelta(days=tage)

    # 4. Daten abrufen
    url_data = (
        f"https://api.opensensemap.org/boxes/{box_id}/data/{sensor_id}"
        f"?from-date={von_datum.strftime('%Y-%m-%dT%H:%M:%SZ')}&to-date={bis_datum.strftime('%Y-%m-%dT%H:%M:%SZ')}&download=false"
    )

    response = requests.get(url_data)
    response.raise_for_status()
    daten_roh = response.json()

    if not daten_roh:
        print("⚠️ Keine historischen Daten gefunden.")
        return None

    df = pd.DataFrame(daten_roh, columns=["createdAt", "value"])
    df['zeitstempel'] = pd.to_datetime(df['createdAt'], errors='coerce')
    df['messwert'] = pd.to_numeric(df['value'], errors='coerce')
    df = df[['zeitstempel', 'messwert']].dropna()
    df['sensor_id'] = sensor_id
    df['box_id'] = box_id

    return df


def verlauf_in_datenbank_schreiben(df):
    """
    Schreibt historische Verlaufsdaten in die Datenbank-Tabelle 'sensor_verlauf'.
    """
    if df is None or df.empty:
        print("⚠️ Keine Verlaufsdaten zum Einfügen.")
        return

    with engine.begin() as conn:
        for _, zeile in df.iterrows():
            conn.execute(text("""
                INSERT INTO sensor_verlauf (
                    zeitstempel, box_id, sensor_id, messwert
                ) VALUES (
                    :zeitstempel, :box_id, :sensor_id, :messwert
                )
                ON CONFLICT (zeitstempel, box_id, sensor_id) DO NOTHING;
            """), {
                "zeitstempel": zeile["zeitstempel"],
                "box_id": zeile["box_id"],
                "sensor_id": zeile["sensor_id"],
                "messwert": zeile["messwert"]
            })


def fetch_daily_min_max(sensor_id, box_id=SENSEBOX_ID):
    query = text("""
        SELECT zeitstempel::date AS datum, MIN(messwert) as min_val, MAX(messwert) as max_val
        FROM sensor_verlauf
        WHERE sensor_id = :sensor_id AND box_id = :box_id
        GROUP BY datum
        ORDER BY datum ASC
    """)
    with engine.connect() as conn:
        df = pd.read_sql(query, conn, params={"sensor_id": sensor_id, "box_id": box_id})
    return df

def create_forecast(df, value_column='min_val', days_ahead=7):
    df_prophet = df[['datum', value_column]].rename(columns={'datum': 'ds', value_column: 'y'})
    df_prophet.dropna(inplace=True)

    model = Prophet(daily_seasonality=True)
    model.fit(df_prophet)

    future = model.make_future_dataframe(periods=days_ahead)
    forecast = model.predict(future)

    return forecast[['ds', 'yhat']].tail(days_ahead)

def fetch_data_today(sensor_id, box_id=SENSEBOX_ID, selection=None, table='sensor_daten', condition=None, orderby=None):
    allowed_columns = ['zeitstempel', 'box_id','sensor_name' ,'sensor_id', 'messwert', 'einheit', 'sensor_typ', 'icon']
    if not set(selection).issubset(allowed_columns):
        raise ValueError("Ungültige Spaltennamen")
    query = text(f"SELECT {', '.join(selection)} FROM {table} WHERE sensor_id = :sensor_id AND box_id = :box_id AND zeitstempel::date = CURRENT_DATE")
    with engine.connect() as conn:
        df = pd.read_sql(query, conn, params={"sensor_id": sensor_id, "box_id": box_id})
    return df