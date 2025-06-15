# Zeigt Countdown bis zur nächsten Live-Aktualisierung
import dash
from dash import dcc, html, Input, Output
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import math
from ml_utils import create_forecast, return_forecast
from sensor_utils import (
    daten_von_api_holen,
    daten_in_datenbank_schreiben,
    verlauf_daten_von_api_holen,
    verlauf_in_datenbank_schreiben,
    box_info_holen,
    fetch_daily_weather_data) 
import os
from sqlalchemy import create_engine, text
import dash_daq as daq
from zoneinfo import ZoneInfo
from astral import LocationInfo
from astral.sun import sun
from datetime import datetime
import pytz
from cards import *
from misc_utils import get_rain_icon, pressure_gauge_figure

# Verbindung zur Datenbank herstellen
DB_URL = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
engine = create_engine(DB_URL)

# SenseBox-ID aus Umgebungsvariable
BOX_ID = os.getenv("SENSEBOX_ID")

# Sensor-IDs definieren
TEMP_SENSOR_ID = "67a661af4ef45d0008682745"  # Temperatur-Sensor-ID
RAIN_SENSOR_ID = "67a7ab164ef45d00089ef795"  # Regen-Sensor-ID

def init_callbacks(app):
    @app.callback(
        Output("countdown", "children"),
        Input("countdown-timer", "n_intervals"),
        Input("daily-model-update", "n_intervals")
    )
    def countdown_timer_render(n_intervals_count, _):
        verbleibend = 180 - (n_intervals_count % 180)
        minuten = verbleibend // 60
        sekunden = verbleibend % 60
        return f"Nächste Aktualisierung in: {minuten:02}:{sekunden:02}"

    # Aktualisiert die Prognose-Grafik täglich
    @app.callback(
        Output("forecast-graph", "children"),
        Input("live-update", "n_intervals")
    )
    def update_forecast_ui(_):
        df = fetch_daily_weather_data(TEMP_SENSOR_ID, RAIN_SENSOR_ID)

        forecast_min = return_forecast(df, 'min_val')
        forecast_max = return_forecast(df, 'max_val')
        forecast_rain = return_forecast(df, 'rain_avg')

        return temperatur_wochenkarte(forecast_min, forecast_max, forecast_rain)

    @app.callback(
        Output("train-dummy-output", "children"),
        Input("daily-model-update", "n_intervals")
    )
    def update_forecast_model(_):

        verlauf_df = verlauf_daten_von_api_holen(TEMP_SENSOR_ID)  # Temperaturverlauf
        verlauf_in_datenbank_schreiben(verlauf_df)

        verlauf_df_rain = verlauf_daten_von_api_holen(RAIN_SENSOR_ID)  # Regenverlauf
        verlauf_in_datenbank_schreiben(verlauf_df_rain)

        df = fetch_daily_weather_data(TEMP_SENSOR_ID, RAIN_SENSOR_ID)

        create_forecast(df, 'max_val')
        create_forecast(df, 'rain_avg')
        create_forecast(df, 'min_val')


    # Aktualisiert die Verlaufsgrafik basierend auf der Sensor-Auswahl im Dropdown
    @app.callback(
        Output("sensor-line-graph", "figure"),
        Input("sensor-dropdown", "value")
    )
    def update_historical_chart(sensor_id):
        df = verlauf_daten_von_api_holen(sensor_id)
        if df is None or df.empty:
            return go.Figure().add_annotation(text="Keine Daten", x=0.5, y=0.5, showarrow=False)

        df["datum"] = df["zeitstempel"].dt.date
        df_agg = df.groupby("datum")["messwert"].mean().reset_index()

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df_agg["datum"],
            y=df_agg["messwert"],
            mode="lines+markers",
            line=dict(color="black"),
            marker=dict(size=6)
        ))

        fig.update_layout(
            margin=dict(t=30, b=30, l=30, r=30),
            height=300,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            xaxis_title="Datum",
            yaxis_title="Messwert"
        )
        return fig


    # Holt aktuelle Temperaturdaten (alle 3 Minuten) und zeigt den letzten Wert an
    @app.callback(
        Output("temperature-thermometer", "value"),
        Output("temperature-display", "children"),
        Input("live-update", "n_intervals")
    )
    def update_temperature_thermometer(_):
        df = daten_von_api_holen()
        if df is None or df.empty:
            return 0, "0°C"

        temp_df = df[df["einheit"] == "°C"]
        if temp_df.empty:
            return 0, "0°C"

        letzter_wert = float(temp_df.sort_values("zeitstempel").iloc[-1]["messwert"])
        return letzter_wert, f"{letzter_wert:.1f}°C"
    

# Aktualisiert das Druckmessgerät (Gauge) mit den letzten Druckdaten
    @app.callback(
        Output("pressure-gauge", "figure"),
        Input("live-update", "n_intervals")
    )
    def update_pressure_gauge(_):
        df = daten_von_api_holen()
        daten_in_datenbank_schreiben(df)
        if df is None or df.empty:
            return go.Figure().add_annotation(text="Keine Druckdaten", x=0.5, y=0.5, showarrow=False)

        pressure_df = df[df["einheit"] == "Pa"]
        if pressure_df.empty:
            return go.Figure().add_annotation(text="Keine Druckdaten", x=0.5, y=0.5, showarrow=False)

        last_value = pressure_df.sort_values("zeitstempel").iloc[-1]["messwert"]
        return pressure_gauge_figure(last_value)

    # Aktualisiert die PM2.5 und PM10 Werte basierend auf der Auswahl im Dropdown
    @app.callback(
        Output("pm-value-display", "children"),
        Input("pm-selector", "value"),
        Input("live-update", "n_intervals")
    )
    def update_pm_value(pm_type, _):
        df = daten_von_api_holen()

        if df is None or df.empty:
            return "Keine PM-Daten"

        pm_ids = {
            "2.5": "67a661af4ef45d000868274b",
            "10":  "67a661af4ef45d000868274c"
        }

        sensor_id = pm_ids[pm_type]

        
        df_filtered = df[df["einheit"] == "µg/m³"]
        pm_df = df_filtered[df_filtered["sensor_id"] == sensor_id]

        if pm_df.empty:
            return f"Keine PM{pm_type} Daten"

        wert = float(pm_df.sort_values("zeitstempel").iloc[-1]["messwert"])
        return f"{wert:.1f} µg/m³"

    # Aktualisiert die Regenmenge und zeigt das passende Icon an
    @app.callback(
        Output("rain-value", "children"),
        Input("live-update", "n_intervals")
    )
    def update_rain_value(_):
        df = daten_von_api_holen()
        if df is None or df.empty:
            return "Keine Daten"

        rain_df = df[df["einheit"] == "mm"]
        if rain_df.empty:
            return "Keine Regendaten"

        latest = rain_df.sort_values("zeitstempel").iloc[-1]["messwert"]
        return f"{latest:.1f} mm"

    # Aktualisiert die Luftfeuchtigkeit und zeigt den letzten Wert an
    @app.callback(
        Output("humidity-value", "children"),
        Input("live-update", "n_intervals")
    )
    def update_humidity_value(_):
        df = daten_von_api_holen()
        if df is None or df.empty:
            return "Keine Daten"

        humidity_df = df[df["einheit"] == "%"]
        if humidity_df.empty:
            return "Keine Feuchtigkeitsdaten"

        latest = humidity_df.sort_values("zeitstempel").iloc[-1]["messwert"]
        return f"{latest:.0f} %"

    # Aktualisiert die Windrose mit dem aktuellen Windrichtung und -geschwindigkeit
    @app.callback(
        Output("wind-gauge", "value"),
        Input("live-update", "n_intervals")
    )
    def update_wind_gauge(_):
        df = daten_von_api_holen()
        if df is None or df.empty:
            return 0, "Keine Daten"

        speed_df = df[df["einheit"] == "kmh"]

        if speed_df.empty:
            return 0, "Keine Winddaten"

        speed = float(speed_df.sort_values("zeitstempel").iloc[-1]["messwert"])

        return speed