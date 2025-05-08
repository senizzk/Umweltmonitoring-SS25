import dash
from dash import dcc, html, Input, Output
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from sensor_utils import (
    daten_von_api_holen,
    daten_in_datenbank_schreiben,
    fetch_daily_min_max,
    create_forecast,
    verlauf_daten_von_api_holen,
    verlauf_in_datenbank_schreiben,
    fetch_data_today
)
from data_fetch import fetch_lastweek_data_auto
from dashboard_objects import *
import os
from sqlalchemy import create_engine, text

# Verbindung zur Datenbank
DB_URL = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
engine = create_engine(DB_URL)

# SenseBox-ID
BOX_ID = os.getenv("SENSEBOX_ID")
sensors_read = pd.read_csv("sensors.csv")
SENSORS = dict(zip(sensors_read["title"], sensors_read["_id"]))
SENSOR_ID_TEMP = SENSORS["Temperature"]
SENSOR_ID_RAIN_H = SENSORS["Rain hourly"]

# Dash App mit Montserrat-Font
app = dash.Dash(__name__, external_stylesheets=[
    dbc.themes.BOOTSTRAP,
    "https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;600;700&display=swap"
])
app.title = "Umweltmonitoring Dashboard"

# 🔧 Gesamtlayout der Seite mit Intervallen für Live-Updates und Modelltraining
app.layout = dbc.Container([
    dcc.Interval(id="daily-model-update", interval=86400 * 1000, n_intervals=0),  # Modell-Update täglich
    dcc.Interval(id="countdown-timer", interval=1000, n_intervals=0),   # Countdown jede Sekunde
    dcc.Interval(id="live-update", interval=180 * 1000, n_intervals=0),  # Live-Daten alle 3 Minuten
    dcc.Interval(id="database-update", interval=60*60*3 * 1000, n_intervals=0),  # Modell-Update täglich

    dbc.Row([
        dbc.Col(live_temperature_card(), md=4),
        dbc.Col(nested_cards(), md=8),
    ], class_name="mb-5"),

    dbc.Row([
        dbc.Col(temperatur_prognose_card(), md=6),
        dbc.Col(verlaufsdiagramm_card(
            sensor_id=SENSOR_ID_TEMP,
            title="Temperaturverlauf (10 Tage)",
            messwert="Temperatur (°C)",
            card_title="📈 Temperatur Verlauf"), md=6)
    ], class_name="mb-4"),

    # Add the live rain card below everything else
    dbc.Row([
    dbc.Col(live_rain_card(), md=4),
    dbc.Col(verlaufsdiagramm_card(
        sensor_id=SENSOR_ID_RAIN_H,
        title="Regenverlauf (10 Tage)",
        messwert="Regenvolum (mm)",
        card_title="📈 Regenverlauf"), md=6)  
], class_name="mb-5"),

    html.Div("Countdown", id="countdown", style={
        "position": "fixed",
        "bottom": "10px",
        "left": "10px",
        "backgroundColor": "#222",
        "color": "#aaa",
        "padding": "10px",
        "borderRadius": "8px",
        "zIndex": "1000"
    }),
    dbc.Row([dbc.Col(update_database_button()), dbc.Col(html.H2(id='live-update-text-db', className="text-center text-primary"))], class_name="mb-5"),
    html.Div(id='dummy-div', style={'display': 'none'})
], fluid=True, class_name="px-5 mt-4")

# Zeigt Countdown bis zur nächsten Live-Aktualisierung
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

# Führt tägliches Training des Vorhersagemodells aus und zeigt die Prognosegrafik
@app.callback(
    Output("forecast-graph", "figure"),
    Input("daily-model-update", "n_intervals")
)   
def update_forecast_figure(_):
    verlauf_df = verlauf_daten_von_api_holen(SENSOR_ID_TEMP)
    verlauf_in_datenbank_schreiben(verlauf_df)

    df = fetch_daily_min_max(SENSOR_ID_TEMP)
    forecast_min = create_forecast(df, 'min_val')
    forecast_max = create_forecast(df, 'max_val')

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=forecast_min['ds'], y=forecast_min['yhat'],
        mode='lines+markers', name='Min Temp.', line=dict(color='blue')
    ))
    fig.add_trace(go.Scatter(
        x=forecast_max['ds'], y=forecast_max['yhat'],
        mode='lines+markers', name='Max Temp.', line=dict(color='red')
    ))
    fig.add_trace(go.Scatter(
        x=forecast_min['ds'], y=forecast_min['yhat'],
        mode='lines', fill='tonexty', showlegend=False,
        fillcolor='rgba(255, 0, 0, 0.1)', line=dict(width=0)
    ))
    fig.update_layout(title="7-Tage-Temperaturvorhersage", height=300)
    return fig

# Holt aktuelle Temperaturdaten (alle 3 Minuten) und zeigt den letzten Wert an
@app.callback(
    Output("live-temperature", "children"),
    Input("live-update", "n_intervals")
)
def update_live_temperature(_):
    df, name = daten_von_api_holen()
    daten_in_datenbank_schreiben(df,box_id = BOX_ID, box_name=name)

    temp_df = df[df["einheit"] == "°C"]
    if temp_df.empty:
        return "- °C"

    letzter_wert = temp_df.sort_values("zeitstempel").iloc[-1]["messwert"]
    return f"{letzter_wert:.1f} °C"

@app.callback(
    Output("live-rain", "children"),
    Input("live-update", "n_intervals")
)
def update_live_rain(_):
    # Fetch the data from the API
    df, name = daten_von_api_holen()

    # Filter for the rain sensor (adjust filter if necessary based on actual sensor type or name)
    rain_df = df[df["sensor_typ"] == "Vevor"]  # Adjust this filter if necessary based on your sensor
    #rain_df = rain_df[rain_df["sensor_name"].str.contains("Rain Hourly")]  # Adjust if necessary

    if rain_df.empty:
        return "- mm"  # No data available

    # Get the most recent value
    letzter_wert = rain_df.sort_values("zeitstempel").iloc[-1]["messwert"]
    return f"{letzter_wert:.1f} mm"  # Format the value as mm

@app.callback(
    Output("dummy-div", "children"),
    Input("database-update", "n_intervals")
)
def update_datenbank(_):
    for sensor_id in SENSORS.values():
        verlauf_df = verlauf_daten_von_api_holen(sensor_id)
        verlauf_in_datenbank_schreiben(verlauf_df)
        # Fetch today's data and write to the database

@app.callback(
    Output("live-update-text-db", "children"),
    Input("update-database-button", "n_clicks")
)
def update_datenbank(_):
    ausgabe = fetch_lastweek_data_auto()
    return f"{ausgabe} Datensätze erfolgreich eingefügt."

# Startet den Dash-Server
if __name__ == "__main__":
    app.run_server(host="0.0.0.0", port=8050, debug=True)