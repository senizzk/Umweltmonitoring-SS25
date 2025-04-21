import dash
from dash import dcc, html, Input, Output
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
app.layout = html.Div([
    dcc.Interval(id="auto-update", interval=UPDATE_INTERVAL_SEKUNDEN * 1000, n_intervals=0),
    dcc.Interval(id="countdown-timer", interval=1000, n_intervals=0),

    html.Div([
        # Temperatur-Box
        html.Div(id="temp-wert", style={
            "width": "320px",
            "height": "320px",
            "padding": "20px 30px",
            "borderRadius": "30px",
            "backgroundColor": "#ECF0F3",
            "boxShadow": "12px 12px 24px #d1d9e6, -12px -12px 24px #ffffff",
            "display": "flex",
            "flexDirection": "column",
            "alignItems": "center",
            "justifyContent": "center",
            "textAlign": "center",
            "zIndex": "1"
        }),

        # Extra-Box mit Sensor-Anzeigen
        # Extra-Box mit Sensor-Anzeigen (üstte 3 büyük, altta 3 küçük Box)
        html.Div([
            # Üstteki 3 büyük kutu
            html.Div([
                html.Div([
                    html.Div("Rain (hourly)", style={
                        "position": "absolute",
                        "top": "15px",
                        "left": "15px",
                        "fontSize": "16px",
                        "fontWeight": "600",
                        "color": "#000"
                    }),
                    html.Div("...", style={
                        "zIndex": "1"
                    })
                ], style={
                    "width": "350px",
                    "height": "280px",
                    #"marginRight": "40px",
                    "borderRadius": "20px",
                    "backgroundColor": "#ECF0F3",
                    "boxShadow": "12px 12px 24px #d1d9e6, -12px -12px 24px #ffffff",
                    "position": "relative",
                    "display": "flex",
                    "alignItems": "center",
                    "justifyContent": "center"
                }),
                html.Div([
                    html.Div("Wind Status", style={
                        "position": "absolute",
                        "top": "15px",
                        "left": "15px",
                        "fontSize": "16px",
                        "fontWeight": "600",
                        "color": "#000"
                    }),
                    html.Div("...", style={
                        "zIndex": "1"
                    })
                ], style={
                    "width": "350px",
                    "height": "280px",
                    #"marginRight": "40px",
                    "borderRadius": "20px",
                    "backgroundColor": "#ECF0F3",
                    "boxShadow": "12px 12px 24px #d1d9e6, -12px -12px 24px #ffffff",
                    "position": "relative",
                    "display": "flex",
                    "alignItems": "center",
                    "justifyContent": "center"
                }),
                html.Div([
                    html.Div("Pressure", style={
                        "position": "absolute",
                        "top": "15px",
                        "left": "15px",
                        "fontSize": "16px",
                        "fontWeight": "600",
                        "color": "#000"
                    }),
                    html.Div("...", style={
                        "zIndex": "1"
                    })
                ], style={
                    "width": "350px",
                    "height": "280px",
                    #"marginRight": "40px",
                    "borderRadius": "20px",
                    "backgroundColor": "#ECF0F3",
                    "boxShadow": "12px 12px 24px #d1d9e6, -12px -12px 24px #ffffff",
                    "position": "relative",
                    "display": "flex",
                    "alignItems": "center",
                    "justifyContent": "center"
                })
            ], style={
                "display": "flex",
                "flexDirection": "row",
                "justifyContent": "center",
                "alignItems": "center",
                "marginBottom": "30px",
                "gap": "40px", 
            }),

            # Alttaki 3 küçük kutu
            html.Div([
                html.Div("Extra 1", style={
                    "width": "350px",
                    "height": "120px",
                    "marginRight": "40px",
                    "borderRadius": "20px",
                    "backgroundColor": "#ECF0F3",
                    "boxShadow": "12px 12px 24px #d1d9e6, -12px -12px 24px #ffffff",
                    "display": "flex",
                    "alignItems": "center",
                    "justifyContent": "center",
                    "fontSize": "16px",
                    "color": "white"
                }),
                html.Div("Extra 2", style={
                    "width": "350px",
                    "height": "120px",
                    "marginRight": "40px",
                    "borderRadius": "20px",
                    "backgroundColor": "#ECF0F3",
                    "boxShadow": "12px 12px 24px #d1d9e6, -12px -12px 24px #ffffff",
                    "display": "flex",
                    "alignItems": "center",
                    "justifyContent": "center",
                    "fontSize": "16px",
                    "color": "white"
                }),
                html.Div("Extra 3", style={
                    "width": "350px",
                    "height": "120px",
                    "borderRadius": "20px",
                    "backgroundColor": "#ECF0F3",
                    "boxShadow": "12px 12px 24px #d1d9e6, -12px -12px 24px #ffffff",
                    "display": "flex",
                    "alignItems": "center",
                    "justifyContent": "center",
                    "fontSize": "16px",
                    "color": "white"
                })
            ], style={
                "display": "flex",
                "flexDirection": "row",
                "justifyContent": "center",
                "alignItems": "center"
            })
        ], style={
            "display": "flex",
            "flexDirection": "column",
            "justifyContent": "space-between",
            "alignItems": "center",
            "width": "1150px",
            "padding": "30px",
            "borderRadius": "30px",
            "backgroundColor": "#ECF0F3",
            "boxShadow": "inset 8px 8px 16px #d1d9e6, inset -8px -8px 16px #ffffff",
            "color": "white",
            "position": "relative",
            "overflow": "hidden",
            "marginLeft": "40px"
        })

    ], style={
        "display": "flex",
        "flexDirection": "row",
        "alignItems": "flex-start",
        "marginTop": "50px",
        "marginLeft": "150px"
    }),

    html.Div(id="countdown", style={
        "position": "fixed",
        "bottom": "20px",
        "left": "20px",
        "backgroundColor": "#eeeeee",
        "padding": "10px 15px",
        "borderRadius": "8px",
        "fontSize": "16px",
        "boxShadow": "1px 1px 6px rgba(0,0,0,0.1)",
        "color": "#333",
        "zIndex": "999"
    })
], style={
    "fontFamily": "'Montserrat', sans-serif",
    "backgroundColor": "#ECF0F3",
    "height": "100vh",
    "width": "100vw",
    "margin": "0",
    "padding": "0",
    "overflow": "hidden"
})

# Temperatur-Callback
@app.callback(
    Output("temp-wert", "children"),
    Input("auto-update", "n_intervals")
)
def aktualisiere_daten(n_intervals):
    df = daten_von_api_holen(BOX_ID)
    daten_in_datenbank_schreiben(df, BOX_ID)

    if df is None or df.empty:
        return html.Div("⚠️ Keine Daten gefunden.", style={"color": "white"})

    temp_df = df[df["einheit"] == "°C"]
    if temp_df.empty:
        return html.Div("⚠️ Keine Temperaturdaten gefunden.", style={"color": "white"})

    letzter_wert = temp_df.sort_values("zeitstempel").iloc[-1]["messwert"]
    zeit = temp_df.sort_values("zeitstempel").iloc[-1]["zeitstempel"]
    zeit_dt = pd.to_datetime(zeit).astimezone(ZoneInfo("Europe/Berlin"))
    zeit_string = zeit_dt.strftime("Stand: %d.%m.%Y – %H:%M")
    wert_text = f"{round(letzter_wert)} °C"

    return [
        html.Div(wert_text, style={
            "fontSize": "50px",
            "fontWeight": "bold",
            "color": "white"
        }),
        html.Hr(style={
            "width": "80%",
            "borderColor": "white",
            "borderWidth": "1px",
            "marginTop": "10px"
        }),
        html.Div(zeit_string, style={
            "fontSize": "14px",
            "color": "#aaa",
            "marginTop": "10px",
            "fontStyle": "italic"
        })
    ]

# Windbox leeren
@app.callback(
    Output("sensor1-box", "children"),
    Input("auto-update", "n_intervals")
)
def leere_windbox(n):
    return ""

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
