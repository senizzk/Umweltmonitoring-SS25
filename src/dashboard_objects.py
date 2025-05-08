import dash
from dash import dcc, html, Input, Output
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
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

def verlaufsdaten_aus_db(sensor_id, box_id=BOX_ID):
    query = text("""
        SELECT zeitstempel, messwert
        FROM sensor_verlauf
        WHERE sensor_id = :sensor_id AND box_id = :box_id
        ORDER BY zeitstempel ASC
    """)
    with engine.connect() as conn:
        df = pd.read_sql(query, conn, params={"sensor_id": sensor_id, "box_id": box_id})
    return df


def verlaufsdiagramm_card(sensor_id, title, messwert, card_title):
    df = verlaufsdaten_aus_db(sensor_id)
    if df.empty:
        fig = go.Figure()
        fig.add_annotation(text="Keine Daten", x=0.5, y=0.5, showarrow=False)
    else:
        fig = px.line(df, x="zeitstempel", y="messwert", title=f"{title}",
                      labels={"zeitstempel": "Zeit", "messwert": f'{messwert}'})
        fig.update_layout(margin=dict(t=30, b=20, l=0, r=0), height=300)

    return dbc.Card(
        dbc.CardBody([
            html.H5(f'{card_title}', className="card-title"),
            dcc.Graph(figure=fig)
        ]),
        class_name="shadow-sm bg-light rounded"
    )


# Leere Karte für die spätere Anzeige der Prognose-Grafik
def temperatur_prognose_card():
    return dbc.Card(
        dbc.CardBody([
            html.H5("📆 7-Tage-Temperaturvorhersage", className="card-title"),
            dcc.Graph(id="forecast-graph")
        ]),
        class_name="shadow-sm bg-light rounded"
    )

# 🔴 Karte zur Anzeige der aktuellen Temperatur
def live_temperature_card():
    return dbc.Card(
        dbc.CardBody([
            html.H5("🌡️ Temperatur", className="card-title"),
            html.H2(id="live-temperature", className="text-center text-primary")
        ]),
        class_name="shadow-sm bg-light rounded",
        style={"height": "150px"}
    )

def live_rain_card():
    return dbc.Card(
        dbc.CardBody([
            html.H5("🌧️ Regen", className="card-title"),
            html.H2(id="live-rain", className="text-center text-primary")
        ]),
        class_name="shadow-sm bg-light rounded",
        style={"height": "150px"}
    )

# Platzhalter-Karte für leere Bereiche im Layout
def placeholder_card(text="Platzhalter-Karte"):
    return dbc.Card(
        dbc.CardBody(html.Div(text, className="text-center text-muted fs-5")),
        class_name="shadow-sm rounded bg-light",
        style={"height": "150px"}
    )

# Flex-Karte für verschachtelte Layouts
def flex_card(text, flex=1):
    return html.Div(
        dbc.Card(
            dbc.CardBody(text, className="text-center text-muted fw-semibold"),
            class_name="shadow-sm bg-light w-100 h-100 rounded"
        ),
        style={"flex": flex, "display": "flex"}
    )

# Erzeugt ein Layout mit mehreren kleinen Karten nebeneinander
def nested_cards():
    return dbc.Card(
        dbc.CardBody([
            html.Div("Kart 2", className="text-muted fs-5 fw-semibold text-center mb-3"),
            dbc.Row([
                dbc.Col([
                    flex_card("Alt Kart 2.1", flex=2),
                    flex_card("Alt Kart 2.4", flex=1)
                ], width=4, style={"display": "flex", "flexDirection": "column", "gap": "0.5rem"}),
                dbc.Col([
                    flex_card("Alt Kart 2.2", flex=2),
                    flex_card("Alt Kart 2.5", flex=1)
                ], width=4, style={"display": "flex", "flexDirection": "column", "gap": "0.5rem"}),
                dbc.Col([
                    flex_card("Alt Kart 2.3", flex=2),
                    flex_card("Alt Kart 2.6", flex=1)
                ], width=4, style={"display": "flex", "flexDirection": "column", "gap": "0.5rem"}),
            ], class_name="g-2")
        ])
    )

def update_database_button():
    return html.Button(
        "Datenbank aktualisieren",
        id="update-database-button",
        className="btn btn-primary",
        style={"margin": "10px"},
        n_clicks=0
    )