import requests
import pandas as pd
from datetime import datetime, timedelta, timezone
import os

def fetch_temperature_auto(senseBoxId, sensorId, csv_path, fallback_start=None):
    # 1. Başlangıç tarihi: ya CSV'deki son createdAt ya da fallback
    if os.path.exists(csv_path):
        df_existing = pd.read_csv(csv_path)
        df_existing["createdAt"] = pd.to_datetime(df_existing["createdAt"], utc=True, errors="coerce")
        df_existing = df_existing.dropna(subset=["createdAt"])
        start_date = df_existing["createdAt"].max()
        print(f"📅 CSV'deki son veri: {start_date}")
    elif fallback_start:
        start_date = fallback_start
        df_existing = pd.DataFrame()
    else:
        raise ValueError("CSV bulunamadı ve fallback_start verilmedi.")

    # 2. Veri çekilecek zaman aralığı
    end_date = datetime.now(timezone.utc)
    current_start = start_date
    all_data = []

    while current_start < end_date:
        current_end = min(current_start + timedelta(days=7), end_date)
        from_str = current_start.strftime("%Y-%m-%dT%H:%M:%S.000Z")
        to_str = current_end.strftime("%Y-%m-%dT%H:%M:%S.000Z")

        url = (
            f"https://api.opensensemap.org/boxes/{senseBoxId}/data/{sensorId}"
            f"?from-date={from_str}&to-date={to_str}&format=json"
        )

        print(f"⬇️ Çekiliyor: {from_str} - {to_str}")
        try:
            response = requests.get(url, timeout=60)
            response.raise_for_status()
            data = response.json()
            print(f"📦 {len(data)} veri alındı.")

            df = pd.DataFrame(data)
            if not df.empty:
                df["createdAt"] = pd.to_datetime(df["createdAt"], utc=True, errors="coerce")
                df["hour"] = df["createdAt"].dt.floor("h")
                df = df.sort_values("createdAt").groupby("hour", as_index=False).tail(1)
                df = df[["createdAt", "value"]]
                all_data.append(df)
        except Exception as e:
            print(f"❌ Hata: {e}")

        current_start = current_end

    if not all_data:
        print("⚠️ Yeni veri yok, dosya güncellenmedi.")
        return df_existing if 'df_existing' in locals() else None

    df_new = pd.concat(all_data, ignore_index=True)

    # 3. Birleştir, temizle, sırala, kaydet
    combined_df = pd.concat([df_existing, df_new], ignore_index=True)
    combined_df = combined_df.drop_duplicates(subset="createdAt")
    combined_df = combined_df.sort_values("createdAt")
    combined_df.to_csv(csv_path, index=False)

    print(f"✅ Güncellendi: {csv_path} ({combined_df.shape[0]} kayıt)")
    return combined_df
