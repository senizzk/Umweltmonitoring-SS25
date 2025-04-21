import dash
from dash import dcc, html, Input, Output
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.graph_objects as go
from sensor_utils import daten_von_api_holen, daten_in_datenbank_schreiben
import os
from sqlalchemy import create_engine
from zoneinfo import ZoneInfo

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

# Funktion für Windrichtungs-Grafik
def wind_figure(direction_deg, speed):
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=[0, 1],
        theta=[direction_deg, direction_deg],
        mode='lines',
        line=dict(color='#00f0ff', width=8),
        hoverinfo='skip'
    ))
    fig.update_layout(
        polar=dict(
            bgcolor="#121212",
            angularaxis=dict(
                direction="clockwise",
                rotation=90,
                showline=False,
                tickfont=dict(color="gray")
            ),
            radialaxis=dict(visible=False)
        ),
        showlegend=False,
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=10, r=10, t=10, b=10)
    )
    return fig

# Layout
app.layout = dbc.Container([
    dbc.Row([
        dbc.Col(
            html.Div(id="temp-wert", style={"color": "black"}),md=4, xl=4, style=
            {"backgroundColor": "aquamarine", "padding": "10px", "borderRadius": "8px", "textAlign": "center"}),
        dbc.Col(
            html.Div("SensorBox1",id="sensor1-box", style={"color": "blue"}),md=4, xl=4),
            ]), 
    dcc.Interval(id="auto-update", interval=UPDATE_INTERVAL_SEKUNDEN * 1000, n_intervals=0),
    dcc.Interval(id="countdown-timer", interval=1000, n_intervals=0),
    html.Div("Countdown",id="countdown", style={
            "position": "fixed",
            "bottom": "10px",
            "left": "10px",
            "backgroundColor": "#222",
            "color": "#aaa",
            "padding": "10px",
            "borderRadius": "8px",
            "zIndex": "1000"})
    ], fluid=True, class_name="mt-4 mx-4")

# Temperatur-Callback
@app.callback(
    Output("temp-wert", "children"),
    Input("auto-update", "n_intervals")
)
def aktualisiere_daten(n_intervals):
    df = daten_von_api_holen(BOX_ID)
    daten_in_datenbank_schreiben(df, BOX_ID)

    if df is None or df.empty:
        return "⚠️ Keine Daten gefunden."

    temp_df = df[df["einheit"] == "°C"]
    if temp_df.empty:
        return "⚠️ Keine Temperaturdaten gefunden."

    letzter_wert = temp_df.sort_values("zeitstempel").iloc[-1]["messwert"]
    zeit = temp_df.sort_values("zeitstempel").iloc[-1]["zeitstempel"]
    zeit_dt = pd.to_datetime(zeit).astimezone(ZoneInfo("Europe/Berlin"))
    zeit_string = zeit_dt.strftime("Stand: %d.%m.%Y – %H:%M")
    wert_text = f"{round(letzter_wert)} °C "

    return wert_text

# Windbox leeren
@app.callback(
    Output("sensor1-box", "children"),
    Input("auto-update", "n_intervals")
)
def leere_windbox(n):
    return "Test-Sensor1"

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
