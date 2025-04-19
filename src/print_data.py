from sensor_utils import daten_von_api_holen

df = daten_von_api_holen()

if df is not None and not df.empty:
    print("📊 Veriler başarıyla alındı!")
    print(df.head(20))  # İlk 20 satırı yazdır
    print("\n📋 Sütunlar:", df.columns.tolist())
    print("\n📈 Benzersiz sensör tipleri:", df["sensor_typ"].unique())
else:
    print("⚠️ Hiç veri gelmedi.")
