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
    create_forecast,
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

# ============================================

# Hilfsfunktion, um das passende Regen-Icon basierend auf der Regenmenge zu erhalten
def get_rain_icon(rain_mm):
    if rain_mm < 0.2:
        return html.I(className="bi bi-sun", style={"fontSize": "1.8rem", "color": "#f7c948"})
    elif rain_mm < 2:
        return html.I(className="bi bi-cloud-sun", style={"fontSize": "1.8rem", "color": "#f0ad4e"})
    elif rain_mm < 5:
        return html.I(className="bi bi-cloud-drizzle", style={"fontSize": "1.8rem", "color": "#17a2b8"})
    elif rain_mm < 10:
        return html.I(className="bi bi-cloud-rain", style={"fontSize": "1.8rem", "color": "#0d6efd"})
    elif rain_mm < 20:
        return html.I(className="bi bi-cloud-rain-heavy", style={"fontSize": "1.8rem", "color": "#0d6efd"})
    else:
        return html.I(className="bi bi-cloud-lightning-rain", style={"fontSize": "1.8rem", "color": "#280452"})


# Erzeugt eine Wochenkarte mit Temperatur- und Regenprognosen
def temperatur_wochenkarte(forecast_min, forecast_max, forecast_rain):
    cards = []

    for i in range(len(forecast_min)):
        day = pd.to_datetime(forecast_min['ds'].iloc[i]).strftime('%A')
        min_temp = forecast_min['yhat'].iloc[i]
        max_temp = forecast_max['yhat'].iloc[i]
        rain = forecast_rain['yhat'].iloc[i]

        rain_icon = get_rain_icon(rain)

        card = dbc.Card([
            dbc.CardBody([
                html.Div(day, className="fw-bold text-center", style={"fontSize": "1.4rem"}),
                html.Div(rain_icon, className="fs-4 text-center"),
                html.Div(f"{round(max_temp)}°", className="text-center fw-bold", style={"fontSize": "1.3rem"}),
                html.Div(f"{round(min_temp)}°", className="text-center text-muted", style={"fontSize": "1.2rem"})
            ])
        ], class_name="text-center glass-card w-100 h-100")

        card_wrapper = html.Div(card, style={"flex": "1 1 0", "minWidth": "90px"})
        cards.append(card_wrapper)

    return html.Div(
        cards,
        style={
            "display": "flex",
            "justifyContent": "center",
            "gap": "15px",
            "flexWrap": "wrap",
            "width": "100%",
        }
    )


# Leere Karte für die spätere Anzeige der Prognose-Grafik
def temperatur_prognose_card():
    return dbc.Card(
        dbc.CardBody([
            html.H5("7-Day Weather Forecast", className="card-title"),
            html.Div(id="forecast-graph")
        ]),
        class_name="glass-card w-100 h-100"
    )

# Berechnet Sonnenaufgang und -untergang für Moste, Slowenien
def calculate_sun_times(lat=46.196912, lon=14.548932):
    city = LocationInfo(
        name="Moste",
        region="Slovenia",
        timezone="Europe/Ljubljana",
        latitude=lat,
        longitude=lon
    )
    timezone = pytz.timezone(city.timezone)
    s = sun(city.observer, date=datetime.now(), tzinfo=timezone)
    sunrise = s["sunrise"].strftime("%H:%M")
    sunset = s["sunset"].strftime("%H:%M")
    return sunrise, sunset

# SenseBox-Info-Karte mit allgemeinen Informationen und Sonnenzeiten
def sensebox_info_card():
    box_info = box_info_holen()
    df = daten_von_api_holen()
    temp_df = df[df["einheit"] == "°C"]
    letzter_temp = temp_df.sort_values("zeitstempel").iloc[-1]
    last_update = letzter_temp["zeitstempel"]
    sunrise, sunset = calculate_sun_times()
    
    name = box_info["name"]
    created_at = box_info["created_at"].replace(tzinfo=ZoneInfo("UTC")).astimezone(ZoneInfo("Europe/Berlin")).strftime('%d-%m-%Y %H:%M')
    exposure = box_info["exposure"]
    last_update = last_update.replace(tzinfo=ZoneInfo("UTC")).astimezone(ZoneInfo("Europe/Berlin")).strftime('%d-%m-%Y %H:%M')

    # Erzeugt die Mini-Karten für Sonnenaufgang und -untergang
    mini_card_1 = dbc.Card(
        dbc.CardBody([
            html.Div(
            html.I(className="bi bi-sunrise-fill", style={"fontSize": "3.6rem", "color": "#FF8C00"}),  
            className="d-flex flex-column justify-content-center align-items-center"
        ),
        html.P(sunrise, className="card-text fw-bold text-center", style={"fontSize": "1.8rem"})
        ]),
        class_name="glass-card w-100 h-100"
    )

    mini_card_2 = dbc.Card(
        dbc.CardBody([
            html.Div(
                html.I(className="bi bi-sunset-fill", style={"fontSize": "3.6rem"}), 
                className="d-flex flex-column justify-content-center align-items-center"
            ),
            html.P(sunset, className="card-text fw-bold text-center", style={"fontSize": "1.8rem"})
        ]),
        class_name="glass-card w-100 h-100"
    )

    mini_cards_row = dbc.Row([
        dbc.Col(mini_card_1, width=6, class_name="h-100"),
        dbc.Col(mini_card_2, width=6, class_name="h-100")
    ], class_name="mt-4 g-1 flex-grow-1 h-100")  

    return dbc.Card(
        dbc.CardBody([
            html.H5(name, className="card-title fw-bold", style={"fontSize": "4rem"}),
            html.Div([
                html.P("Created on:", className="mb-0",style={"fontSize": "1.3rem"}),
                html.P(created_at, className="mb-2"),
                html.P("Location type:", className="mb-0",style={"fontSize": "1.3rem"}),
                html.P(exposure, className="mb-2"),
                html.P("Last updated:", className="mb-0",style={"fontSize": "1.3rem"}),
                html.P(last_update, className="mb-0"),
            ], className="text-muted"),
            mini_cards_row  
        ]),
        class_name="glass-card w-100 h-100"
    )


# Platzhalter-Karte für leere Bereiche
def placeholder_card(text="Platzhalter-Karte"):
    return dbc.Card(
        dbc.CardBody(html.Div(text, className="text-center text-muted fs-5")),
        class_name="glass-card w-100 h-100",
        style={"height": "150px"}
    )

# Erzeugt eine flexible Karte, die in einem flexiblen Layout verwendet werden kann
def flex_card(text, flex=1):
    return html.Div(
        dbc.Card(
            dbc.CardBody(text, className="text-center text-muted fw-semibold"),
            class_name="glass-card w-100 h-100"
        ),
            style={
            "flex": flex,
            "display": "flex",
            "height": "100%",
            "minHeight": "220px",
            "maxHeight": "350px"
        }
    )

# Erzeugt eine Karte mit mehreren Karten für verschiedene Sensoren
def nested_cards():
    return dbc.Card(
        dbc.CardBody([
            html.Div("Today's Highlight", className="fw-semibold text-center"),
            dbc.Row([
                dbc.Col([
                    html.Div(
                        dbc.Card(
                            dbc.CardBody([
                                html.H5([
                                    html.I(className="bi bi-thermometer-half me-2"),
                                    "Temperature"
                                ], className="card-title mb-3"),
                                html.Div([
                                    daq.Thermometer(
                                        id="temperature-thermometer",
                                        min=-15,
                                        max=50,
                                        value=0,
                                        showCurrentValue=False,
                                        color="black",
                                        style={
                                        "position": "absolute",
                                        "top": "50%",
                                        "left": "40%",
                                        "transform": "translate(-50%, -50%)",
                                    }
                                    ),
                                    html.Div(
                                        id="temperature-display",
                                        style={
                                            "fontSize": "2rem",
                                            "marginLeft": "20px",
                                            "color": "black",
                                            "position": "absolute",
                                            "top": "52%",
                                            "left": "60%",
                                            "transform": "translate(-50%, -50%)"
                                       }
                                    )
                                ],
                                style={
                                    "display": "flex",
                                    "justifyContent": "center",
                                    "alignItems": "center",
                                })
                            ],
                            style={    
                                "minHeight": "300px",        
                                "overflow": "hidden"
                            }),
                            class_name="glass-card w-100 h-100"
                        ),
                        style={"flex": 3, "display": "flex", "justifyContent": "center"}
                    ),

                    html.Div(
                        dbc.Card(
                            dbc.CardBody([
                                html.H5([
                                html.I(className="bi bi-cloud-rain-fill me-2", style={"color": "black"}),  
                                "Rain"
                            ], className="card-title"),

                                html.H2(id="rain-value", className="text-center",
                                            style={
                                                "fontSize": "2rem",
                                                "marginLeft": "20px",
                                                "color": "black",
                                                "marginTop": "19px"
                                            })
                            ]),
                            class_name="glass-card w-100 h-100"
                        ),
                        style={"flex": 2, "display": "flex"}
                    ),
                ], width=4, style={"display": "flex", "flexDirection": "column", "gap": "0.5rem"}),
                dbc.Col([
                    html.Div(
                        dbc.Card(
                            dbc.CardBody([
                                html.H5([
                                    html.I(className="bi bi-wind me-2", style={"color": "black"}),
                                    "Wind Speed"
                                ], className="card-title mb-3"),

                                html.Div(
                                    daq.Gauge(
                                        id="wind-gauge",
                                        min=0,
                                        max=40,
                                        value=0,
                                        color="black",
                                        showCurrentValue=True,
                                        units="km/h",
                                        size=220 
                                    ),
                                    style={
                                        "position": "absolute",
                                        "top": "65%",
                                        "left": "50%",
                                        "transform": "translate(-50%, -50%)",
                                        "zIndex": 1      
                                    }
                                ),
                                html.Div(style={"height": "227px"})  
                            ]),
                            class_name="glass-card w-100 h-100 position-relative"
                        ),
                        style={"flex": 1, "display": "flex", "justifyContent": "center"}
                    ),

                    html.Div(
                        dbc.Card(
                            dbc.CardBody([
                                html.H5([
                                html.I(className="bi bi-droplet me-2", style={"color": "black"}),  
                                "Humidity"
                            ]),
                                html.H2(id="humidity-value", className="text-center",
                                            style={
                                                "fontSize": "2rem",
                                                "marginLeft": "20px",
                                                "color": "black",
                                                "marginTop": "19px"

                                            })
                            ]),
                            class_name="glass-card w-100 h-100"
                        ),
                        style={"flex": 3, "display": "flex"}
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
                                dcc.Graph(id="pressure-gauge", config={"displayModeBar": False} , 
                                          style={"height": "235px"}) 
                ]),
                            class_name="glass-card w-100 h-100"
                        ),
                        style={"flex": 3, "display": "flex"}
                    ),
                    html.Div(
                    dbc.Card(
                        dbc.CardBody([ 
                            dbc.Row([
                                dbc.Col(html.H5("Particulate Type", className="card-title"), width="auto"),	
                                dbc.Col(
                                    dcc.RadioItems(
                                        id="pm-selector",
                                        options=[
                                            {"label": "PM2.5", "value": "2.5"},
                                            {"label": "PM10", "value": "10"}
                                        ],
                                        value="2.5",
                                        inline=True,
                                        inputStyle={"margin-right": "6px", "margin-left": "10px"}
                                    ),
                                    width="auto"
                                )
                            ], className="align-items-center mb-2"),

                            html.Div(id="pm-value-display", className="text-center",
                                style={
                                    "fontSize": "2rem",
                                    "marginLeft": "20px",
                                    "color": "black"
                                })
                        ]),
                        class_name="glass-card w-100 h-100"
                    ),
                    style={"flex": 2, "display": "flex"}
                )], width=4, style={"display": "flex", "flexDirection": "column", "gap": "0.5rem"}),
            ], class_name="g-2")
        ]), class_name="glass-card w-100 h-100"
    )

# ============================================

# Erzeugt ein Druckmessgerät (Gauge) für die Anzeige des Luftdrucks
def pressure_gauge_figure(pressure_value):
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=pressure_value,
        number={"suffix": "Pa", "font": {"size": 32, "color": "black", "family": "sans-serif"}},
        gauge={
            'axis': {'range': [90000, 110000], 'tickwidth': 1, 'tickcolor': "gray"},
            'bar': {'color': "black"},
            'borderwidth': 0,
            'bgcolor': "rgb(230, 230, 230)",
        },
        domain={'x': [0, 1], 'y': [0, 1]}
    ))

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",  
        margin=dict(t=50, b=40, l=30, r=30),
        height=220
    )
    return fig

# ============================================

# Gesamtlayout der Seite mit Intervallen für Live-Updates und Modelltraining
app.layout = dbc.Container([
    dcc.Interval(id="daily-model-update", interval=86400 * 1000, n_intervals=0),  # Modell-Update täglich
    dcc.Interval(id="countdown-timer", interval=1000, n_intervals=0),   # Countdown jede Sekunde
    dcc.Interval(id="live-update", interval=180 * 1000, n_intervals=0),  # Live-Daten alle 3 Minuten

    html.H1("Dashboard", className="display-4 mb-4 text-center fw-bold"),

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

# Aktualisiert die Prognose-Grafik täglich
@app.callback(
    Output("forecast-graph", "children"),
    Input("daily-model-update", "n_intervals")
)
def update_forecast_ui(_):
    verlauf_df = verlauf_daten_von_api_holen(TEMP_SENSOR_ID)  # Temperaturverlauf
    verlauf_in_datenbank_schreiben(verlauf_df)

    verlauf_df_rain = verlauf_daten_von_api_holen(RAIN_SENSOR_ID)  # Regenverlauf
    verlauf_in_datenbank_schreiben(verlauf_df_rain)

    df = fetch_daily_weather_data(TEMP_SENSOR_ID, RAIN_SENSOR_ID)

    forecast_min = create_forecast(df, 'min_val')
    forecast_max = create_forecast(df, 'max_val')
    forecast_rain = create_forecast(df, 'rain_avg')

    return temperatur_wochenkarte(forecast_min, forecast_max, forecast_rain)


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



# Startet den Dash-Server
if __name__ == "__main__":
    app.run_server(host="0.0.0.0", port=8050, debug=True)
