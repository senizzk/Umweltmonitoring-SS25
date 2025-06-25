import dash
from dash import dcc, html
import dash_bootstrap_components as dbc
import os
from sqlalchemy import create_engine
from cards import *

# Verbindung zur Datenbank herstellen
DB_URL = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
engine = create_engine(DB_URL)

# SenseBox-ID aus Umgebungsvariable
BOX_ID = os.getenv("SENSEBOX_ID")

# Sensor-IDs definieren
TEMP_SENSOR_ID = "67a661af4ef45d0008682745"  # Temperatur-Sensor-ID
RAIN_SENSOR_ID = "67a7ab164ef45d00089ef795"  # Regen-Sensor-ID

# Dash-App initialisieren mit Bootstrap-Theme und Google Fonts (Montserrat)
app = dash.Dash(__name__, external_stylesheets=[
    dbc.themes.BOOTSTRAP,  # Bootstrap CSS für Layout und Komponenten
    "https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.5/font/bootstrap-icons.css"  # Bootstrap Icons laden
])


app.title = "Umweltmonitoring Dashboard"


app.layout = dbc.Container([
    dcc.Interval(id="daily-model-update", interval=86400 * 1000, n_intervals=0),  # Modell-Update täglich
    dcc.Interval(id="countdown-timer", interval=1000, n_intervals=0),   # Countdown jede Sekunde
    dcc.Interval(id="live-update", interval=180 * 1000, n_intervals=0),  # Live-Daten alle 3 Minuten

    html.H1("Umweltmonitoring Dashboard", className="display-4 mb-4 text-center fw-bold"),

    dbc.Row([
        dbc.Col(
            sensebox_info_card(), 
            md=4, 
            class_name="h-100"
        ),
        dbc.Col(
            nested_cards(), 
            md=8, 
            class_name="h-100"
        ),
    ], class_name="mb-5 align-items-stretch"),

    dbc.Row([
        dbc.Col(temperatur_prognose_card())
    ], class_name="mb-4"),

    dbc.Row([
    dbc.Col(verlauf_graph_card())
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
    html.Div(id="train-dummy-output", style={"display": "none"})
], fluid=True, class_name="px-5 mt-4")

from callbacks import init_callbacks

init_callbacks(app)  # Initialisiere die Callbacks

if __name__ == "__main__":
    app.run_server(host="0.0.0.0", port=8050, debug=True)
