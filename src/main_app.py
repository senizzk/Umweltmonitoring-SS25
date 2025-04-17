import dash
from dash import dcc, html, Input, Output
import plotly.graph_objs as go
import pandas as pd
from sensor_utils import daten_von_api_holen, daten_in_datenbank_schreiben

import os
from sqlalchemy import create_engine

# 🛠️ Verbindung zur Datenbank aufbauen
DB_URL = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
engine = create_engine(DB_URL)

# 🌍 SenseBox ID
BOX_ID = os.getenv("SENSEBOX_ID")

# 🧠 Dash App starten
app = dash.Dash(__name__)
app.title = "Umweltmonitoring Dashboard"

# 📐 Layout definieren
app.layout = html.Div([
    html.H1("Umweltüberwachung (Gruppe Eins)", style={"textAlign": "center"}),

    html.Button("📡 Daten aktualisieren", id="update-button", n_clicks=0),
    html.Div(id="update-info", children="Noch keine Daten geladen."),

    dcc.Graph(id="daten-grafik")
])

# 🔁 Callback: Bei Button-Klick → Daten abrufen und anzeigen
@app.callback(
    Output("daten-grafik", "figure"),
    Output("update-info", "children"),
    Input("update-button", "n_clicks")
)
def aktualisiere_daten(n_clicks):
    if n_clicks == 0:
        raise dash.exceptions.PreventUpdate

    # 1. Daten von API holen
    df = daten_von_api_holen(BOX_ID)

    # 2. In die Datenbank schreiben
    daten_in_datenbank_schreiben(df, BOX_ID)

    # 3. Für die Anzeige vorbereiten
    if df is None or df.empty:
        return go.Figure(), "⚠️ Keine Daten gefunden."

    fig = go.Figure()

    for sensor_id, gruppe in df.groupby("sensor_id"):
        fig.add_trace(go.Scatter(
            x=gruppe["zeitstempel"],
            y=gruppe["messwert"],
            mode="lines+markers",
            name=f"{gruppe['sensor_typ'].iloc[0]} ({gruppe['einheit'].iloc[0]})"
        ))

    fig.update_layout(
        title="Messwerte der SenseBox",
        xaxis_title="Zeit",
        yaxis_title="Messwert",
        template="plotly_white"
    )

    return fig, f"✅ {len(df)} Messungen aktualisiert."

# 🚀 App starten
if __name__ == "__main__":
    app.run_server(host="0.0.0.0", port=8050, debug=True)
