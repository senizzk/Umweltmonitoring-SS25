# test_verlauf_import.py

from sensor_utils import verlauf_daten_von_api_holen, verlauf_in_datenbank_schreiben
import pandas as pd
from sqlalchemy import create_engine, text 
import os

# Sensor ID (sıcaklık)
sensor_id = "60a048f7a877b3001b1f9996"

# 1. Veriyi API'den al
df = verlauf_daten_von_api_holen(sensor_id)

# 2. Terminalde göster
print("📊 API'den gelen veri:")
print(df.head())

# 3. Veritabanına yaz
verlauf_in_datenbank_schreiben(df)

# 4. DB'den kontrol için veri çek
DB_URL = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
engine = create_engine(DB_URL)

with engine.connect() as conn:
    result = conn.execute(text("SELECT * FROM sensor_verlauf ORDER BY zeitstempel DESC LIMIT 5"))
    print("\n✅ Veritabanındaki son 5 satır:")
    for row in result:
        print(row)
