import dash
from dash import dcc, html, Input, Output
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.graph_objects as go
from sensor_utils import daten_von_api_holen, daten_in_datenbank_schreiben
import os
from sqlalchemy import create_engine
from zoneinfo import ZoneInfo
from dash_iconify import DashIconify
import plotly.express as px

# Verbindung zur Datenbank
DB_URL = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
engine = create_engine(DB_URL)

# SenseBox-ID
BOX_ID = os.getenv("SENSEBOX_ID")

# Dash App mit Montserrat-Font
app = dash.Dash(__name__, external_stylesheets=[
    dbc.themes.BOOTSTRAP,
    "https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;600;700&display=swap"
])
app.title = "Umweltmonitoring Dashboard"

# Aktualisierungsintervall
UPDATE_INTERVAL_SEKUNDEN = 180

# Neumorph Style Placeholder Card
def placeholder_card(text="Boş Kart"):
    return dbc.Card(
        dbc.CardBody(html.Div(text, className="text-center text-muted fs-5")),
        class_name="shadow-sm rounded bg-light",
        style={"height": "150px"}
    )

def flex_card(text, flex=1):
    return html.Div(
        dbc.Card(
            dbc.CardBody(text, className="text-center text-muted fw-semibold"),
            class_name="shadow-sm bg-light w-100 h-100 rounded"
        ),
        style={"flex": flex, "display": "flex"}
    )

def nested_cards():
    return dbc.Card(
        dbc.CardBody([
            html.Div("Kart 2", className="text-muted fs-5 fw-semibold text-center mb-3"),

            dbc.Row([
                # Sütun 1
                dbc.Col([
                    flex_card("Alt Kart 2.1", flex=2),
                    flex_card("Alt Kart 2.4", flex=1)
                ], width=4, style={"display": "flex", "flexDirection": "column", "gap": "0.5rem"}),

                # Sütun 2
                dbc.Col([
                    flex_card("Alt Kart 2.2", flex=2),
                    flex_card("Alt Kart 2.5", flex=1)
                ], width=4, style={"display": "flex", "flexDirection": "column", "gap": "0.5rem"}),

                # Sütun 3
                dbc.Col([
                    flex_card("Alt Kart 2.3", flex=2),
                    flex_card("Alt Kart 2.6", flex=1)
                ], width=4, style={"display": "flex", "flexDirection": "column", "gap": "0.5rem"}),
            ], class_name="g-2")
        ])
    )



# Layout mit 2x2 leeren Karten
app.layout = dbc.Container([
    dcc.Interval(id="auto-update", interval=UPDATE_INTERVAL_SEKUNDEN * 1000, n_intervals=0),
    dcc.Interval(id="countdown-timer", interval=1000, n_intervals=0),

    dbc.Row([
        dbc.Col(placeholder_card("Kart 1"), md=4),
        dbc.Col(nested_cards(), md=8),
    ], class_name="mb-5"),

    dbc.Row([
        dbc.Col(placeholder_card("Kart 3"), md=6),
        dbc.Col(placeholder_card("Kart 4"), md=6),
    ], class_name="mb-4"),

    html.Div("Countdown", id="countdown", style={
        "position": "fixed",
        "bottom": "10px",
        "left": "10px",
        "backgroundColor": "#222",
        "color": "#aaa",
        "padding": "10px",
        "borderRadius": "8px",
        "zIndex": "1000"
    })
], fluid=True, class_name="px-5 mt-4")


# Countdown-Callback
@app.callback(
    Output("countdown", "children"),
    Input("countdown-timer", "n_intervals"),
    Input("auto-update", "n_intervals")
)
def countdown_timer_render(n_intervals_count, n_intervals_update):
    sekunden_seit_update = n_intervals_count % UPDATE_INTERVAL_SEKUNDEN
    verbleibend = UPDATE_INTERVAL_SEKUNDEN - sekunden_seit_update
    minuten = verbleibend // 60
    sekunden = verbleibend % 60
    return f"Nächste Aktualisierung in: {minuten:02}:{sekunden:02}"

# App starten
if __name__ == "__main__":
    app.run_server(host="0.0.0.0", port=8050, debug=True)
