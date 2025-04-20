import dash
from dash import dcc, html, Input, Output
import pandas as pd
from sensor_utils import daten_von_api_holen, daten_in_datenbank_schreiben
import os
from sqlalchemy import create_engine
from zoneinfo import ZoneInfo

# 📦 Verbindung zur Datenbank
DB_URL = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
engine = create_engine(DB_URL)

# 🌍 SenseBox-ID aus Umgebungsvariablen
BOX_ID = os.getenv("SENSEBOX_ID")

# 🚀 Dash-App starten mit Montserrat Schriftart
app = dash.Dash(__name__, external_stylesheets=[
    "https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;600;700&display=swap"
])
app.title = "Umweltmonitoring Dashboard"

# 🔁 Aktualisierungsintervall (in Sekunden)
UPDATE_INTERVAL_SEKUNDEN = 180  # alle 3 Minuten

# 🧱 App-Layout
app.layout = html.Div([

    # ⏱️ Automatische Aktualisierung + Countdown
    dcc.Interval(id="auto-update", interval=UPDATE_INTERVAL_SEKUNDEN * 1000, n_intervals=0),
    dcc.Interval(id="countdown-timer", interval=1000, n_intervals=0),

    # 📊 Zeile mit zwei Boxen: Temperatur + weitere Infos
    html.Div([
        # 🌡️ Temperaturbox
        html.Div(id="temp-wert",
                 style={
                     "position": "relative",
                     "padding": "20px 30px",
                     "borderRadius": "40px",
                     "boxShadow": "2px 2px 12px rgba(0,0,0,0.3)",
                     "width": "320px",
                     "height": "420px",
                     "display": "flex",
                     "flexDirection": "column",
                     "alignItems": "center",
                     "justifyContent": "center",
                     "textAlign": "center",
                     "overflow": "hidden",
                     "zIndex": "1",
                     "background": "linear-gradient(135deg, rgba(18, 18, 89, 0.3), rgba(75, 0, 130, 0.3), rgba(138, 43, 226, 0.3), rgba(135,206,250, 0.3))"
                 }),

        # 📦 Zusatzbox (z. B. für Grafiken, Vorhersagen, weitere Sensoren)
        html.Div(id="extra-box",
                 children="Hier könnten weitere Inhalte stehen...",
                 style={
                     "width": "1120px",
                     "height": "420px",
                     "padding": "20px 30px",
                     "marginLeft": "30px",
                     "borderRadius": "40px",
                     "background": "linear-gradient(135deg, rgba(18, 18, 89, 0.3), rgba(75, 0, 130, 0.3), rgba(138, 43, 226, 0.3), rgba(135,206,250, 0.3))",
                     "color": "white",
                     "display": "flex",
                     "alignItems": "center",
                     "justifyContent": "center",
                     "fontSize": "24px",
                     "boxShadow": "2px 2px 12px rgba(0,0,0,0.2)"
                 })
    ], style={
        "display": "flex",
        "flexDirection": "row",
        "alignItems": "flex-start",
        "marginTop": "50px",
        "marginLeft": "150px"
    }),

    # 🕒 Countdown unten links
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
    "backgroundColor": "#000000",
    "height": "100vh",
    "width": "100vw",
    "margin": "0",
    "padding": "0",
    "overflow": "hidden"
})

# 🔄 Callback zur Aktualisierung der Temperaturbox
@app.callback(
    Output("temp-wert", "children"),
    Input("auto-update", "n_intervals")
)
def aktualisiere_daten(n_intervals):
    # 📥 Neue Daten von der API abrufen und in DB schreiben
    df = daten_von_api_holen(BOX_ID)
    daten_in_datenbank_schreiben(df, BOX_ID)

    if df is None or df.empty:
        return html.Div("⚠️ Keine Daten gefunden.", style={"color": "white"})

    # 🔍 Nur Temperaturdaten filtern
    temp_df = df[df["einheit"] == "°C"]
    if temp_df.empty:
        return html.Div("⚠️ Keine Temperaturdaten gefunden.", style={"color": "white"})

    # 🌡️ Letzter Messwert + Zeitstempel
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

# ⏳ Callback für Countdown zur nächsten Aktualisierung
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

# 🧪 Server starten
if __name__ == "__main__":
    app.run_server(host="0.0.0.0", port=8050, debug=True)
