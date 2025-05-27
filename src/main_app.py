import dash
from dash import dcc, html, Input, Output
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import math
from sensor_utils import (
    daten_von_api_holen,
    daten_in_datenbank_schreiben,
    fetch_daily_min_max,
    create_forecast,
    verlauf_daten_von_api_holen,
    verlauf_in_datenbank_schreiben,
    box_info_holen)
import os
from sqlalchemy import create_engine, text

# Verbindung zur Datenbank
DB_URL = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
engine = create_engine(DB_URL)

# SenseBox-ID
BOX_ID = os.getenv("SENSEBOX_ID")
SENSOR_ID = "67a661af4ef45d0008682745"

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

def temperatur_wochenkarte(forecast_min, forecast_max):
    cards = []

    for i in range(len(forecast_min)):
        day = pd.to_datetime(forecast_min['ds'].iloc[i]).strftime('%a')  # 'Mon', 'Tue' ...
        min_temp = forecast_min['yhat'].iloc[i]
        max_temp = forecast_max['yhat'].iloc[i]

        card = dbc.Card([
            dbc.CardBody([
                html.Div(day, className="fw-bold text-center"),
                html.Div("🌦️", className="fs-3 text-center"),  # Hava durumu ikonu (istersen değiştirilebilir)
                html.Div(f"{round(max_temp)}°", className="text-center fw-bold"),
                html.Div(f"{round(min_temp)}°", className="text-center text-muted")
            ])
        ], class_name="text-center shadow-sm bg-light", style={"width": "100px", "margin": "0 5px"})

        cards.append(card)

    return html.Div(cards, style={"display": "flex", "justifyContent": "center", "gap": "10px"})


# Leere Karte für die spätere Anzeige der Prognose-Grafik
def temperatur_prognose_card():
    return dbc.Card(
        dbc.CardBody([
            html.H5("📆 7-Tage-Temperaturvorhersage", className="card-title"),
            html.Div(id="forecast-graph")
        ]),
        class_name="shadow-sm bg-light rounded"
    )

def sensebox_info_card():
    box_info = box_info_holen()

    name = box_info["name"]
    created_at = box_info["created_at"].strftime('%Y-%m-%d %H:%M') if box_info["created_at"] else "Unbekannt"
    exposure = box_info["exposure"]

    return dbc.Card(
        dbc.CardBody([
            html.H5(name, className="card-title"),
            html.Div([
                html.P(f"Erstellt am: {created_at}", className="mb-1"),
                html.P(f"Standorttyp: {exposure}", className="mb-0")
            ], className="text-muted")
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
                    html.Div(
                        dbc.Card(
                            dbc.CardBody([
                                html.H5("🌡️ Temperatur", className="card-title"),
                                html.H2(id="live-temperature", className="text-center text-primary")
                            ]),
                            class_name="shadow-sm bg-light w-100 h-100 rounded"
                        ),
                        style={"flex": 2, "display": "flex"}
                    ),
                    html.Div(
                        dbc.Card(
                            dbc.CardBody([
                                html.H5("🌧️ Regen", className="card-title"),
                                html.H2(id="rain-value", className="text-center text-primary")
                            ]),
                            class_name="shadow-sm bg-light w-100 h-100 rounded"
                        ),
                        style={"flex": 1, "display": "flex"}
                    ),
                ], width=4, style={"display": "flex", "flexDirection": "column", "gap": "0.5rem"}),
                dbc.Col([
                    html.Div(
                        dbc.Card(
                            dbc.CardBody([
                                html.H5([
                                    html.I(className="bi bi-wind me-2"),
                                    "Wind"
                                ], className="card-title mb-2"),
                                dcc.Graph(id="wind-arrow", config={"displayModeBar": False}, style={"height": "220px"})
                            ]),
                            class_name="shadow-sm bg-light w-100 h-100 rounded"
                        ),
                        style={"flex": 2, "display": "flex"}
                    ),
                    html.Div(
                        dbc.Card(
                            dbc.CardBody([
                                html.H5("💧 Luftfeuchtigkeit", className="card-title"),
                                html.H2(id="humidity-value", className="text-center text-primary")
                            ]),
                            class_name="shadow-sm bg-light w-100 h-100 rounded"
                        ),
                        style={"flex": 1, "display": "flex"}
                    )
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
        number={"suffix": "Pa", "font": {"size": 24}},
        gauge={
            'axis': {'range': [90000, 110000], 'tickwidth': 1, 'tickcolor': "gray"},
            'bar': {'color': "royalblue"},
            'borderwidth': 1
        },
        domain={'x': [0, 1], 'y': [0, 1]}
    ))

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",  # ❗ Grafiğin dış kutusu saydam
        plot_bgcolor="rgba(0,0,0,0)",   # ❗ İç alan (grafik arkası) da saydam
        margin=dict(t=30, b=30, l=30, r=30),
        height=220
    )
    return fig


def wind_arrow_rose_chart(direction_deg, speed_kmh):
    fig = go.Figure()

    fig.add_trace(go.Barpolar(
        r=[speed_kmh],
        theta=[direction_deg],
        name=f"{speed_kmh:.1f} km/h",
        marker_color='skyblue',
        opacity=0.8
    ))

    fig.update_layout(
        template=None,
        polar=dict(
            radialaxis=dict(range=[0, max(10, speed_kmh + 2)], showticklabels=True, ticks='', angle=45),
            angularaxis=dict(
                rotation=90,
                direction="clockwise",
                tickmode='array',
                tickvals=[0, 45, 90, 135, 180, 225, 270, 315],
                ticktext=["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
            )
        ),
        showlegend=False,
        margin=dict(t=20, b=20, l=20, r=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)"
    )

    return fig


# 🔧 Gesamtlayout der Seite mit Intervallen für Live-Updates und Modelltraining
app.layout = dbc.Container([
    dcc.Interval(id="daily-model-update", interval=86400 * 1000, n_intervals=0),  # Modell-Update täglich
    dcc.Interval(id="countdown-timer", interval=1000, n_intervals=0),   # Countdown jede Sekunde
    dcc.Interval(id="live-update", interval=180 * 1000, n_intervals=0),  # Live-Daten alle 3 Minuten

    html.H1("Dashboard", className="display-4 mb-4 text-center fw-bold"),

    dbc.Row([
        dbc.Col(sensebox_info_card(), md=4),
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
    Output("forecast-graph", "children"),
    Input("daily-model-update", "n_intervals")
)
def update_forecast_ui(_):
    verlauf_df = verlauf_daten_von_api_holen(SENSOR_ID)
    verlauf_in_datenbank_schreiben(verlauf_df)

    df = fetch_daily_min_max(SENSOR_ID)
    forecast_min = create_forecast(df, 'min_val')
    forecast_max = create_forecast(df, 'max_val')

    return temperatur_wochenkarte(forecast_min, forecast_max)


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
        "2.5": "67a661af4ef45d000868274b",
        "10":  "67a661af4ef45d000868274c"
    }

    sensor_id = pm_ids[pm_type]

    # Sadece µg/m³ olanları al, sonra doğru ID'yi filtrele
    df_filtered = df[df["einheit"] == "µg/m³"]
    pm_df = df_filtered[df_filtered["sensor_id"] == sensor_id]

    if pm_df.empty:
        return f"Keine PM{pm_type} Daten"

    wert = float(pm_df.sort_values("zeitstempel").iloc[-1]["messwert"])
    return f"PM{pm_type}: {wert:.1f} µg/m³"

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

@app.callback(
    Output("wind-arrow", "figure"),
    Input("live-update", "n_intervals")
)
def update_wind_arrow(_):
    df = daten_von_api_holen()
    if df is None or df.empty:
        return go.Figure().add_annotation(text="Keine Daten", x=0.5, y=0.5, showarrow=False)

    speed_df = df[df["einheit"] == "kmh"]
    dir_df = df[df["einheit"] == "°"]

    if speed_df.empty or dir_df.empty:
        return go.Figure().add_annotation(text="Keine Winddaten", x=0.5, y=0.5, showarrow=False)

    speed = float(speed_df.sort_values("zeitstempel").iloc[-1]["messwert"])
    direction = float(dir_df.sort_values("zeitstempel").iloc[-1]["messwert"])

    return wind_arrow_rose_chart(direction, speed)  





# Startet den Dash-Server
if __name__ == "__main__":
    app.run_server(host="0.0.0.0", port=8050, debug=True)
