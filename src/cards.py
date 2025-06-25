import pandas as pd
import dash_bootstrap_components as dbc
from dash import html, dcc
from datetime import datetime
from astral.sun import sun
from astral import LocationInfo
import pytz
from zoneinfo import ZoneInfo
from sensor_utils import *
from misc_utils import * 
import dash_daq as daq

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
            html.H5("7-Day Weather Forecast", className="card-title text-center"),
            html.Div(id="forecast-graph")
        ]),
        class_name="glass-card w-100 h-100"
    )
# Verlaufsgrafik-Karte mit Dropdown zur Sensor-Auswahl
def verlauf_graph_card():
    return dbc.Card(
        dbc.CardBody([
        html.H5("7-Day History", className="card-title text-center mb-3"),
        html.Div(
            dcc.Dropdown(
                id="sensor-dropdown",
                options=[
                    {"label": "Temperature (°C)", "value": "67a661af4ef45d0008682745"},
                    {"label": "Pressure (Pa)", "value": "67a661af4ef45d0008682746"},
                    {"label": "Rain (mm)", "value": "67a7ab164ef45d00089ef795"},
                    {"label": "Humidity (%)", "value": "67a661af4ef45d0008682748"},
                    {"label": "Wind speed (km/h)", "value": "67a661af4ef45d0008682749"},
                    {"label": "PM 2.5 (µg/m³)", "value": "67a661af4ef45d000868274b"},
                    {"label": "PM 10 (µg/m³)", "value": "67a661af4ef45d000868274c"}
                ],
                value="67a661af4ef45d0008682745",
                clearable=False,
            ),
            style={
                "maxWidth": "300px",       
                "margin": "0 auto",         
                "marginBottom": "20px"
            }
        ),
        dcc.Graph(id="sensor-line-graph", config={"displayModeBar": False})
    ]), class_name="glass-card w-100 h-100"
        ),


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
    sunrise, sunset = calculate_sun_times()

    name = box_info["name"]
    created_at = box_info["created_at"].replace(
        tzinfo=ZoneInfo("UTC")
    ).astimezone(ZoneInfo("Europe/Berlin")).strftime('%d-%m-%Y %H:%M')
    exposure = box_info["exposure"]

    # Mini-Karten für Sonnenaufgang und -untergang
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
                html.P("Created on:", className="mb-0", style={"fontSize": "1.3rem"}),
                html.P(created_at, className="mb-2"),
                html.P("Location type:", className="mb-0", style={"fontSize": "1.3rem"}),
                html.P(exposure, className="mb-2"),
                html.P("Last updated:", className="mb-0", style={"fontSize": "1.3rem"}),
                html.P(id="last-updated-text", className="mb-0"),  
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
