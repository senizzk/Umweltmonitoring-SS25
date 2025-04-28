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

def sensor_card(icon, label, id, unit, color="#007bff"):
    return dbc.Card(
        dbc.CardBody([
            html.Div([
                DashIconify(icon=icon, width=28, color=color, className="me-2"),
                html.Span(label, className="fs-5 fw-semibold"),  #fs-5 für größere Schriftgröße, fw-semibold für fetten Text
            ], className="d-flex align-items-center mb-3"),

            html.Div([
                html.Span(id=id, className="fs-1 fw-bold me-2"),
                html.Span(unit, className="fs-2 text-muted")
            ], className="d-flex align-items-end")
        ]),
        class_name="p-3", style={
            "boxShadow": "inset 0 2px 6px rgba(0, 0, 0, 0.1)",
            "borderRadius": "0.5rem",
            "backgroundColor": "#f8f9fa"
        },
    )


def temperaturverlauf_karte(dataframe):
    fig = px.line(dataframe, x="Zeit", y="Temperatur", title=None, markers=True)
    fig.update_layout(
        margin=dict(l=0, r=0, t=0, b=0),
        height=250,
        plot_bgcolor="#f8f9fa",
        paper_bgcolor="#f8f9fa",
        font=dict(color="#343a40"),
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True, gridcolor="#dee2e6")
    )

    return dbc.Card(
        dbc.CardBody([
            html.Div([
                DashIconify(icon="mdi:chart-line", width=28, className="me-2", color="#6f42c1"),
                html.Span("Temperaturverlauf", className="fs-5 fw-semibold"),
            ], className="d-flex align-items-center mb-3"),
            dcc.Graph(figure=fig, config={"displayModeBar": False})
        ]),
        class_name="shadow-sm rounded bg-light"
    )



app.layout = dbc.Container([
    html.H4("Wetter Dashboard", className="mb-4"),

    dbc.Row([
        dbc.Col(sensor_card("mdi:thermometer", "Temperatur", "temp-wert", "°C", "#dc3545"), md=4),
        dbc.Col(sensor_card("mdi:weather-windy", "Wind", "wind-wert", "km/h", "#0d6efd"), md=4),
        dbc.Col(sensor_card("mdi:weather-rainy", "Regen", "regen-wert", "mm", "#198754"), md=4),
    ], class_name="gx-4 gy-4"),

    dcc.Interval(id="auto-update", interval=UPDATE_INTERVAL_SEKUNDEN * 1000, n_intervals=0),
    dcc.Interval(id="countdown-timer", interval=1000, n_intervals=0),
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
], fluid=True, class_name="mt-4")

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
    wert_text = f"{round(letzter_wert)}"

    return wert_text

# Windbox leeren
@app.callback(
    Output("wind-wert", "children"),
    Input("auto-update", "n_intervals")
)
def leere_windbox(n):
    return "Windbox"

@app.callback(
    Output("regen-wert", "children"),
    Input("auto-update", "n_intervals")
)
def regen_anzeigen(n):
    return "Regenbox"


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
