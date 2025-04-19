import dash
from dash import dcc, html, Input, Output
import pandas as pd
from sensor_utils import daten_von_api_holen, daten_in_datenbank_schreiben
import os
from sqlalchemy import create_engine

# Veritabanı bağlantısı
DB_URL = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
engine = create_engine(DB_URL)

# SenseBox ID
BOX_ID = os.getenv("SENSEBOX_ID")

# Dash başlat
app = dash.Dash(__name__)
app.title = "Umweltmonitoring Dashboard"

UPDATE_INTERVAL_SEKUNDEN = 180  # 3 dakika

# Layout
app.layout = html.Div([

    # Otomatik güncellemeler
    dcc.Interval(id="auto-update", interval=UPDATE_INTERVAL_SEKUNDEN * 1000, n_intervals=0),
    dcc.Interval(id="countdown-timer", interval=1000, n_intervals=0),

    # Sıcaklık kutusu (içeriği callback ile güncellenir)
    html.Div(id="temp-wert",
             style={
                 "position": "relative",
                 "top": "20px",
                 "left": "50px",
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

    # Geri sayım kutusu
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
    "backgroundColor": "#000000",  # Siyah tam ekran arka plan
    "height": "100vh",
    "width": "100vw",
    "margin": "0",
    "padding": "0",
    "overflow": "hidden"
})

# Sıcaklık kutusunu güncelleyen callback
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
        })
    ]

# Geri sayımı güncelleyen callback
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

# Uygulamayı başlat
if __name__ == "__main__":
    app.run_server(host="0.0.0.0", port=8050, debug=True)
