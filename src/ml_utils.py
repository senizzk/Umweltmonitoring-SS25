import os
import requests
import pandas as pd
from sqlalchemy import create_engine, text
from datetime import datetime, timedelta, timezone
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
    df_prophet = df[['datum', value_column]].rename(columns={'datum': 'ds', value_column: 'y'})
    df_prophet.dropna(inplace=True)

    model = Prophet(daily_seasonality=True)
    model.fit(df_prophet)

    with open(f'model_{value_column}.pkl', 'wb') as f:
        pickle.dump(model, f)

def return_forecast(df, value_column='min_val', days_ahead=7):
    

    with open(f'model_{value_column}.pkl', 'rb') as f:
        model = pickle.load(f)
    future = model.make_future_dataframe(periods=days_ahead)
    forecast = model.predict(future)

    return forecast[['ds', 'yhat']].tail(days_ahead)