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
    verlauf_in_datenbank_schreiben
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
    "https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;600;700&display=swap",
    "https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.5/font/bootstrap-icons.css"
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
            style={
            "flex": flex,
            "display": "flex",
            "height": "100%",
            "minHeight": "220px",
            "maxHeight": "350px"
        }
    )

# Erzeugt ein Layout mit mehreren kleinen Karten nebeneinander
def nested_cards():
    return dbc.Card(
        dbc.CardBody([
            html.Div("Today's Highlight", className="text-muted fs-5 fw-semibold text-center mb-3"),
            dbc.Row([
                dbc.Col([
                    flex_card("Alt Kart 2.1", flex=2),
                    flex_card("Alt Kart 2.4", flex=1)
                ], width=4, style={"display": "flex", "flexDirection": "column", "gap": "0.5rem"}),
                dbc.Col([
                    html.Div(
                        dbc.Card(
                            dbc.CardBody([
                                html.H5([
                                    html.I(className="bi bi-wind me-2"),
                                    "Wind"
                                ], className="card-title mb-2")
                            ]),
                            class_name="shadow-sm bg-light w-100 h-100 rounded"
                        ),
                        style={"flex": 2, "display": "flex"}
                    ),
                    flex_card("Alt Kart 2.5", flex=1)
                ], width=4, style={"display": "flex", "flexDirection": "column", "gap": "0.5rem"}),
                dbc.Col([
                    html.Div(
                        dbc.Card(
                            dbc.CardBody([
                                html.H5([
                                    html.I(className="bi bi-speedometer2 me-2"),
                                    "Pressure"
                                ], className="card-title mb-2"),
                                dcc.Graph(id="pressure-gauge", config={"displayModeBar": False})
                ]),
                            class_name="shadow-sm bg-light w-100 h-100 rounded"
                        ),
                        style={"flex": 2, "display": "flex"}
                    ),
                    html.Div(
                        dbc.Card(
                            dbc.CardBody([
                                html.Div([
                                    html.Label("Particulate Type", className="fw-semibold mb-1"),
                                    dcc.RadioItems(
                                        id="pm-selector",
                                        options=[
                                            {"label": "PM2.5", "value": "2.5"},
                                            {"label": "PM10", "value": "10"}
                                        ],
                                        value="2.5",
                                        inline=True,
                                        inputStyle={"margin-right": "6px", "margin-left": "10px"}
                                    )
                                ], className="mb-3"),
                                html.Div(id="pm-value-display", className="fs-4 text-center fw-bold text-primary")
                            ]),
                            class_name="shadow-sm bg-light w-100 h-100 rounded"
                        ),
                        style={"flex": 1, "display": "flex"}
                    )


                ], width=4, style={"display": "flex", "flexDirection": "column", "gap": "0.5rem"}),
            ], class_name="g-2")
        ])
    )

def pressure_gauge_figure(pressure_value):
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=pressure_value,
        number={"suffix": " Pa"},
        gauge={
            "axis": {"range": [90000, 110000], "tickwidth":1},
            "bar": {"color": "royalblue","thickness": 0.8},
            "threshold": {
                "line": {"color": "blue", "width": 4},
                "thickness": 0.75,
                "value": pressure_value
            }
        },
        domain={"x": [0, 1], "y": [0, 0.8]}
    ))
    fig.update_layout(margin=dict(t=0, b=0, l=0, r=0), height=170)
    return fig



# 🔧 Gesamtlayout der Seite mit Intervallen für Live-Updates und Modelltraining
app.layout = dbc.Container([
    dcc.Interval(id="daily-model-update", interval=86400 * 1000, n_intervals=0),  # Modell-Update täglich
    dcc.Interval(id="countdown-timer", interval=1000, n_intervals=0),   # Countdown jede Sekunde
    dcc.Interval(id="live-update", interval=180 * 1000, n_intervals=0),  # Live-Daten alle 3 Minuten

    html.H1("Dashboard", className="display-4 mb-4 text-center fw-bold"),

    dbc.Row([
        dbc.Col(live_temperature_card(), md=4),
        dbc.Col(nested_cards(), md=8),
    ], class_name="mb-5"),

    dbc.Row([
        dbc.Col(temperatur_prognose_card(), md=6),
        dbc.Col(verlaufsdiagramm_card(SENSOR_ID), md=6),
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
    df = daten_von_api_holen()
    daten_in_datenbank_schreiben(df)

    temp_df = df[df["einheit"] == "°C"]
    if temp_df.empty:
        return "- °C"

    letzter_wert = temp_df.sort_values("zeitstempel").iloc[-1]["messwert"]
    return f"{letzter_wert:.1f} °C"

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
        "2.5": "60a04b94a877b3001b20d26c",
        "10":  "60a04b94a877b3001b20d26d"
    }

    sensor_id = pm_ids[pm_type]

    # Sadece µg/m³ olanları al, sonra doğru ID'yi filtrele
    df_filtered = df[df["einheit"] == "µg/m³"]
    pm_df = df_filtered[df_filtered["sensor_id"] == sensor_id]

    if pm_df.empty:
        return f"Keine PM{pm_type} Daten"

    wert = float(pm_df.sort_values("zeitstempel").iloc[-1]["messwert"])
    return f"PM{pm_type}: {wert:.1f} µg/m³"





# Startet den Dash-Server
if __name__ == "__main__":
    app.run_server(host="0.0.0.0", port=8050, debug=True)
