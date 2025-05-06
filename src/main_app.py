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
import os
from sqlalchemy import create_engine, text

# Verbindung zur Datenbank
DB_URL = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
engine = create_engine(DB_URL)

# SenseBox-ID
BOX_ID = os.getenv("SENSEBOX_ID")
SENSOR_ID = "60a048f7a877b3001b1f9996"

# Dash App mit Montserrat-Font
app = dash.Dash(__name__, external_stylesheets=[
    dbc.themes.BOOTSTRAP,
    "https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;600;700&display=swap"
])
app.title = "Umweltmonitoring Dashboard"

# Holt historische Messdaten aus der Datenbank für einen Sensor

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

# Erzeugt eine Karte mit einem Liniendiagramm zum Temperaturverlauf

def verlaufsdiagramm_card(sensor_id):
    df = verlaufsdaten_aus_db(sensor_id)

    if df.empty:
        fig = go.Figure()
        fig.add_annotation(text="Keine Daten", x=0.5, y=0.5, showarrow=False)
    else:
        fig = px.line(df, x="zeitstempel", y="messwert", title="Temperaturverlauf (10 Tage)",
                      labels={"zeitstempel": "Zeit", "messwert": "Temperatur (°C)"})
        fig.update_layout(margin=dict(t=30, b=20, l=0, r=0), height=300)

    return dbc.Card(
        dbc.CardBody([
            html.H5("📈 Temperatur Verlauf", className="card-title"),
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

# 🔧 Gesamtlayout der Seite mit Intervallen für Live-Updates und Modelltraining
app.layout = dbc.Container([
    dcc.Interval(id="daily-model-update", interval=86400 * 1000, n_intervals=0),  # Modell-Update täglich
    dcc.Interval(id="countdown-timer", interval=1000, n_intervals=0),   # Countdown jede Sekunde
    dcc.Interval(id="live-update", interval=180 * 1000, n_intervals=0),  # Live-Daten alle 3 Minuten

    dbc.Row([
        dbc.Col(live_temperature_card(), md=4),
        dbc.Col(nested_cards(), md=8),
    ], class_name="mb-5"),

    dbc.Row([
        dbc.Col(temperatur_prognose_card(), md=6),
        dbc.Col(verlaufsdiagramm_card(SENSOR_ID), md=6),
    ], class_name="mb-4"),

    # Add the live rain card below everything else
    dbc.Row([
    dbc.Col(live_rain_card(), md=4),  # Add rain card here
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
    })
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
    verlauf_df = verlauf_daten_von_api_holen(SENSOR_ID)
    verlauf_in_datenbank_schreiben(verlauf_df)

    df = fetch_daily_min_max(SENSOR_ID)
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
    daten_in_datenbank_schreiben(df)

    temp_df = df[df["einheit"] == "°C"]
    if temp_df.empty:
        return "- °C"

    letzter_wert = temp_df.sort_values("zeitstempel").iloc[-1]["messwert"]
    return f"{letzter_wert:.1f} °C"

@app.callback(
    Output("live-rain", "children"),
    Input("live-update", "n_intervals")
)
def update_live_rain():
    # Fetch the data from the API
    df, name = daten_von_api_holen()

    # Filter for the rain sensor (adjust filter if necessary based on actual sensor type or name)
    rain_df = df[df["sensor_typ"] == "Vevor"]  # Adjust this filter if necessary based on your sensor
    rain_df = rain_df[rain_df["sensor_name"].str.contains("Rain Hourly")]  # Adjust if necessary

    if rain_df.empty:
        return "- mm"  # No data available

    # Get the most recent value
    letzter_wert = rain_df.sort_values("zeitstempel").iloc[-1]["messwert"]
    return f"{letzter_wert:.1f} mm"  # Format the value as mm


# Startet den Dash-Server
if __name__ == "__main__":
    app.run_server(host="0.0.0.0", port=8050, debug=True)