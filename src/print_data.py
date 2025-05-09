from sensor_utils import verlauf_daten_von_api_holen

df = verlauf_daten_von_api_holen('67a661af4ef45d0008682745')

if df is not None and not df.empty:
    print("📊 Veriler başarıyla alındı!")
    print(df.tail(20))  # İlk 20 satırı yazdır
    print("\n📋 Sütunlar:", df.columns.tolist())
else:
    print("⚠️ Hiç veri gelmedi.")
