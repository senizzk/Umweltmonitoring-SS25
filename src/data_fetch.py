import requests
import pandas as pd
from datetime import datetime, timedelta, timezone
import os
from sqlalchemy import create_engine
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import text

BOX_ID = os.getenv("BOX_ID")
sensors_info = pd.read_csv("sensors.csv")
SENSORS = dict(zip(sensors_info["title"], sensors_info["_id"]))

DB_URL = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
engine = create_engine(DB_URL)

def insert_on_conflict_do_nothing(table, conn, keys, data_iter):
    """
    Insert data into the database, ignoring conflicts.
    """
    data = [dict(zip(keys, row)) for row in data_iter] 
    stmt = insert(table.table).values(data).on_conflict_do_nothing(index_elements=["zeitstempel", "sensor_id", "box_id"])
    result = conn.execute(stmt)
    return result.rowcount

def fetch_lastweek_data_auto():
    for sensor_name, sensor_id in SENSORS.items():
        to_date = datetime.now(timezone.utc)
        from_date = to_date - timedelta(days=7)
        to_date = to_date.strftime("%Y-%m-%dT%H:%M:%S.000Z")
        from_date = from_date.strftime("%Y-%m-%dT%H:%M:%S.000Z")
        url = f"https://api.opensensemap.org/boxes/{BOX_ID}/data/{sensor_id}?from-date={from_date}&to-date={to_date}&format=json"
        try:
            response = requests.get(url, timeout=60)
            response.raise_for_status()
            data = response.json()
            df = pd.DataFrame(data)
            df = df.drop(columns=["location"])
            df = df.rename(columns={"createdAt": "zeitstempel", "value": "messwert"})
            if not df.empty:
                df["zeitstempel"] = pd.to_datetime(df["zeitstempel"], utc=True, errors="coerce")
                df["box_id"] = BOX_ID
                df["messwert"] = pd.to_numeric(df["messwert"], errors="coerce")
                df["sensor_id"] = sensor_id
                df["sensor_name"] = sensor_name
                df["einheit"] = sensors_info[sensors_info["_id"] == sensor_id]["unit"].values[0]
                df["sensor_typ"] = sensors_info[sensors_info["_id"] == sensor_id]["sensorType"].values[0]
                df["icon"] = sensors_info[sensors_info["_id"] == sensor_id]["icon"].values[0]
                rows_inserted = df.to_sql("sensor_daten", engine, if_exists="append", method=insert_on_conflict_do_nothing, index=False,chunksize=1000)
                with open("data_log.txt", "a") as log_file:
                    log_file.write(f"{datetime.now()}: {sensor_name} - {rows_inserted} Datensätze erfolgreich eingefügt.\n")
        except Exception as e:
            print(f"Fehler: {e}")
            continue

        