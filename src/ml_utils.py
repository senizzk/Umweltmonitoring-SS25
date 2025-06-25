import os
from prophet import Prophet
import pickle

# Umgebungsvariablen für die Datenbankverbindung
DB_USER = os.getenv("DB_USER", "gruppeeins")
DB_PASSWORD = os.getenv("DB_PASSWORD", "mypassword")
DB_HOST = os.getenv("DB_HOST", "db")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "umwelt_db")

# SenseBox-ID (von OpenSenseMap)
SENSEBOX_ID = os.getenv("SENSEBOX_ID", "67a661af4ef45d0008682744")


def create_forecast(df, value_column='min_val', days_ahead=7):
    # Wählt die Spalten 'datum' und die angegebene Wertspalte aus, benennt sie für Prophet um
    df_prophet = df[['datum', value_column]].rename(columns={'datum': 'ds', value_column: 'y'})
    
    # Entfernt Zeilen mit fehlenden Werten
    df_prophet.dropna(inplace=True)

    # Erstellt ein Prophet-Modell mit täglicher Saisonalität
    model = Prophet(daily_seasonality=True)
    
    # Trainiert das Modell 
    model.fit(df_prophet)

    # Speichert das trainierte Modell in einer Datei zur späteren Nutzung
    with open(f'model_{value_column}.pkl', 'wb') as f:
        pickle.dump(model, f)

def return_forecast(df, value_column='min_val', days_ahead=7):
    # Lädt das gespeicherte Modell aus der Datei
    with open(f'model_{value_column}.pkl', 'rb') as f:
        model = pickle.load(f)

    # Erstellt ein DataFrame mit zukünftigen Zeitpunkten, für die eine Prognose gemacht wird
    future = model.make_future_dataframe(periods=days_ahead)

    # Führt die Vorhersage mit dem geladenen Modell durch
    forecast = model.predict(future)

    # Gibt die letzten 'days_ahead' Tage der Vorhersage zurück (mit Datum und Prognosewert)
    return forecast[['ds', 'yhat']].tail(days_ahead)