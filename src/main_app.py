import dash
from dash import dcc, html, Input, Output
import plotly.graph_objs as go
import pandas as pd
from sensor_utils import daten_von_api_holen, daten_in_datenbank_schreiben
import os
from sqlalchemy import create_engine

# 🛠️ Datenbankverbindung
DB_URL = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
engine = create_engine(DB_URL)

# 🌍 SenseBox ID
BOX_ID = os.getenv("SENSEBOX_ID")

# 🧠 Dash App starten
app = dash.Dash(__name__)
app.title = "Umweltmonitoring Dashboard"

UPDATE_INTERVAL_SEKUNDEN = 180  # 3 dakika

# 📐 Layout
app.layout = html.Div([
    html.H1("Umweltüberwachung (Gruppe Eins)", style={"textAlign": "center"}),

    # Otomatik güncelleme & sayaç
    dcc.Interval(id="auto-update", interval=UPDATE_INTERVAL_SEKUNDEN * 1000, n_intervals=0),
    dcc.Interval(id="countdown-timer", interval=1000, n_intervals=0),

    # Bilgi ve sıcaklık kutuları
    html.Div(id="update-info", style={"textAlign": "center", "marginTop": "10px"}),

    html.Div(
    id="temp-wert",
    
    style={
        "position": "absolute",
        "top": "20px",
        "left": "50px",
        "background": "linear-gradient(160deg, #1e3c72, #2a5298, #5b86e5, #4b79a1, #283e51)",
        "padding": "20px 30px",
        "borderRadius": "40px",
        "boxShadow": "2px 2px 12px rgba(0,0,0,0.1)",
        "fontSize": "50px",
        "fontWeight": "bold",
        "color": "#fff",  # beyaz yazı
        "width": "320px",
        "height": "420px",
        "display": "flex",
        "alignItems": "center",         # DİKEY ORTALA
        "justifyContent": "flex-start", # YATAY SOL
        "textAlign": "left"
    }
    ),

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
])

# 🔁 Verileri güncelleyen callback
@app.callback(
    Output("update-info", "children"),
    Output("temp-wert", "children"),
    Input("auto-update", "n_intervals")
)
def aktualisiere_daten(n_intervals):
    df = daten_von_api_holen(BOX_ID)
    daten_in_datenbank_schreiben(df, BOX_ID)

    if df is None or df.empty:
        return "⚠️ Keine Daten gefunden.", ""

    temp_df = df[df["einheit"] == "°C"]
    if temp_df.empty:
        return "⚠️ Keine Temperaturdaten gefunden.", ""

    letzter_wert = temp_df.sort_values("zeitstempel").iloc[-1]["messwert"]
    wert_text = f"{round(letzter_wert)} °C"

    return f"✅ {len(df)} Messungen aktualisiert.", wert_text

# ⏳ Geri sayımı yöneten callback
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

# 🚀 App starten
if __name__ == "__main__":
    app.run_server(host="0.0.0.0", port=8050, debug=True)
